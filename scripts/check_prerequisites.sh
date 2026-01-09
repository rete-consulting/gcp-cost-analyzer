#!/usr/bin/env bash
#
# check_prerequisites.sh - Validate environment before GCP cost analysis
#
# Purpose: Stop before making assumptions. Verify all requirements are met.
#
# This script prevents the #1 mistake from the original analysis:
# Making assumptions when requirements aren't met.
#
# Usage: ./check_prerequisites.sh <project_id>
#

set -euo pipefail

PROJECT_ID="${1:-}"
ERRORS=0

echo "=========================================="
echo "GCP Cost Analyzer - Prerequisites Check"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
error() {
    echo -e "${RED}✗ FAIL:${NC} $1" >&2
    ((ERRORS++))
}

success() {
    echo -e "${GREEN}✓ PASS:${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠ WARN:${NC} $1"
}

info() {
    echo "  → $1"
}

# Check 1: Project ID provided
echo "1. Checking project ID..."
if [ -z "$PROJECT_ID" ]; then
    error "No project ID provided"
    info "Usage: $0 <project_id>"
    exit 1
else
    success "Project ID: $PROJECT_ID"
fi
echo ""

# Check 2: gcloud CLI installed
echo "2. Checking gcloud CLI..."
if ! command -v gcloud &> /dev/null; then
    error "gcloud CLI not found"
    info "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
else
    GCLOUD_VERSION=$(gcloud version --format="value(core)" 2>/dev/null || echo "unknown")
    success "gcloud CLI installed (version: $GCLOUD_VERSION)"
fi
echo ""

# Check 3: Authentication
echo "3. Checking authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    error "No active gcloud authentication"
    info "Run: gcloud auth login"
    info "Run: gcloud auth application-default login"
else
    ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | head -n1)
    success "Authenticated as: $ACTIVE_ACCOUNT"
fi
echo ""

# Check 4: Project exists and accessible
echo "4. Checking project access..."
if ! gcloud projects describe "$PROJECT_ID" &> /dev/null; then
    error "Cannot access project: $PROJECT_ID"
    info "Possible reasons:"
    info "  - Project doesn't exist"
    info "  - You don't have permissions"
    info "  - Project ID is misspelled"
    info "Check: gcloud projects list"
else
    PROJECT_NAME=$(gcloud projects describe "$PROJECT_ID" --format="value(name)" 2>/dev/null)
    success "Project accessible: $PROJECT_NAME"
fi
echo ""

# Check 5: Required APIs enabled
echo "5. Checking required APIs..."
REQUIRED_APIS=(
    "monitoring.googleapis.com:Cloud Monitoring API"
    "cloudfunctions.googleapis.com:Cloud Functions API"
    "cloudbilling.googleapis.com:Cloud Billing API"
)

for api_spec in "${REQUIRED_APIS[@]}"; do
    IFS=':' read -r api_name api_display <<< "$api_spec"

    if gcloud services list --enabled --project="$PROJECT_ID" --filter="name:$api_name" --format="value(name)" 2>/dev/null | grep -q "$api_name"; then
        success "$api_display enabled"
    else
        error "$api_display NOT enabled"
        info "Enable with: gcloud services enable $api_name --project=$PROJECT_ID"
    fi
done
echo ""

# Check 6: Billing account linked
echo "6. Checking billing account..."
if BILLING_ACCOUNT=$(gcloud billing projects describe "$PROJECT_ID" --format="value(billingAccountName)" 2>/dev/null) && [ -n "$BILLING_ACCOUNT" ]; then
    success "Billing account linked: $BILLING_ACCOUNT"
else
    warning "No billing account linked or cannot verify"
    info "Some cost data may not be available"
fi
echo ""

# Check 7: Permissions
echo "7. Checking IAM permissions..."
REQUIRED_ROLES=(
    "monitoring.viewer:Monitoring Viewer"
    "cloudfunctions.viewer:Cloud Functions Viewer"
)

PERMISSION_ISSUES=0
for role_spec in "${REQUIRED_ROLES[@]}"; do
    IFS=':' read -r role_id role_display <<< "$role_spec"

    # Note: We can't easily check specific roles without complex IAM queries
    # Instead, we'll try to access resources that require these permissions
    # This is a best-effort check
    info "Required role: $role_display"
done
warning "Permission check is best-effort - actual API calls will validate access"
echo ""

# Check 8: Python availability (for cost calculation scripts)
echo "8. Checking Python..."
if ! command -v python3 &> /dev/null; then
    error "Python 3 not found"
    info "Required for cost calculation scripts"
else
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    success "Python 3 installed (version: $PYTHON_VERSION)"

    # Check Python version >= 3.8
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        warning "Python version is ${PYTHON_VERSION}, but 3.8+ recommended"
    fi
fi
echo ""

# Check 9: Optional tools
echo "9. Checking optional tools..."
if command -v jq &> /dev/null; then
    success "jq installed (JSON processing)"
else
    warning "jq not found (optional, but recommended)"
    info "Install for better output: brew install jq (macOS) or apt-get install jq (Linux)"
fi
echo ""

# Summary
echo "=========================================="
echo "Prerequisites Check Summary"
echo "=========================================="
echo ""

if [ $ERRORS -eq 0 ]; then
    success "All critical checks passed!"
    echo ""
    echo "✓ Ready to analyze GCP costs for project: $PROJECT_ID"
    echo ""
    exit 0
else
    error "Found $ERRORS critical issue(s)"
    echo ""
    echo "✗ Cannot proceed with analysis until issues are resolved"
    echo ""
    exit 1
fi
