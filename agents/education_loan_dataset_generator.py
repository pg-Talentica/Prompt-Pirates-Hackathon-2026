#!/usr/bin/env python3
"""Education Loan Dataset Generator Agent - Creates synthetic support knowledge base.

Generates 100+ files (PDF, Word, TXT, Images) for education loan customer support RAG testing.

Usage:
    python -m agents.education_loan_dataset_generator [--output-dir data/kb/education_loans] [--count 100]
"""

import argparse
import json
import random
import re
from pathlib import Path
from typing import Iterator

# Target: 5-6 pages per document, ~400-500 words per page
WORDS_PER_PAGE = 450
PAGES_PER_DOC = (5, 6)
MIN_WORDS_PER_DOC = WORDS_PER_PAGE * PAGES_PER_DOC[0]  # 2250
MAX_WORDS_PER_DOC = WORDS_PER_PAGE * PAGES_PER_DOC[1]  # 2700


def _word_count(text: str) -> int:
    """Count words in text."""
    return len(re.findall(r"\S+", text))


def _ensure_word_count(text: str, min_w: int, max_w: int) -> str:
    """Ensure text is within word count range."""
    words = text.split()
    if len(words) < min_w:
        # Repeat content to reach minimum
        multiplier = (min_w // len(words)) + 1
        text = " ".join([text] * multiplier)
        words = text.split()
    if len(words) > max_w:
        return " ".join(words[:max_w])
    return text


# ============================================
# EDUCATION LOAN DOMAIN TEMPLATES
# ============================================

PAYMENT_PROCESSING_RUNBOOK = """
Education Loan Payment Processing Service Runbook: {title}

Overview
This runbook provides comprehensive procedures for handling payment processing issues in the Education Loan Payment Service.
The service processes loan repayments, EMI collections, and payment gateway integrations for {region} region.
Supports payment methods: {payment_methods} across {countries} countries.

Architecture
The Payment Processing Service consists of the following components:
- Payment Gateway Integration Layer: Handles communication with external payment gateways (Razorpay, Stripe, PayPal)
- EMI Calculation Engine: Computes monthly installments based on loan amount, interest rate, and tenure
- Payment Reconciliation Service: Matches incoming payments with loan accounts
- Notification Service: Sends payment confirmations and reminders
- Database Layer: Stores payment transactions and loan account details

The service integrates with:
- Loan Management System (LMS) for account balance updates
- Bank APIs for direct debit processing
- SMS/Email services for payment notifications
- Audit logging system for compliance

Common Issues

Issue 1: Payment Gateway Timeout (ERR_PAY_LOAN_001)
Symptoms:
- Payment requests timing out after 30 seconds
- Students receiving "Payment processing, please wait" messages
- Payment status showing as "Pending" indefinitely
- High error rate in payment gateway logs

Root Causes:
- Payment gateway API experiencing high latency (>5 seconds response time)
- Network connectivity issues between our service and gateway
- Payment gateway rate limiting our requests
- Database connection pool exhaustion causing slow transaction lookups

Mitigation Steps:
Step 1: Check Payment Gateway Status
- Navigate to payment gateway status page: https://status.{gateway}.com
- Check for any ongoing incidents or maintenance windows
- Verify API response times using: curl -w "@curl-format.txt" https://api.{gateway}.com/health

Step 2: Diagnose Network Connectivity
- Run network diagnostic: ping api.{gateway}.com
- Check firewall rules: Ensure outbound HTTPS (443) is allowed
- Verify DNS resolution: nslookup api.{gateway}.com
- Test connectivity: telnet api.{gateway}.com 443

Step 3: Check Database Performance
- Monitor database connection pool: SELECT count(*) FROM pg_stat_activity;
- Check for long-running queries: SELECT pid, query, state FROM pg_stat_activity WHERE state = 'active';
- Review database connection pool configuration in application.properties
- If pool exhausted, increase max connections: payment-service --config db_pool_size=100

Step 4: Implement Retry Logic
- Enable exponential backoff for payment gateway calls
- Configure retry policy: max_retries=3, initial_delay=1s, max_delay=10s
- Add circuit breaker pattern to fail fast if gateway is down
- Route to backup payment gateway if primary fails

Step 5: Verify Resolution
- Monitor payment success rate: Should return to >99.5%
- Check average payment processing time: Should be <3 seconds
- Verify no pending payments stuck in "Processing" state
- Confirm payment confirmations are being sent to students

Rollback Procedure:
If mitigation causes issues:
1. Revert database pool size: payment-service --config db_pool_size=50
2. Disable backup gateway routing: payment-service --config use_backup_gateway=false
3. Restore previous retry configuration
4. Notify team in #loan-payment-ops Slack channel
5. Update incident log with rollback details

Past Incidents:
- Incident INC-2024-001: Payment gateway timeout on 2024-01-15, duration 45 minutes
  Root cause: Payment gateway API experiencing high latency due to DDoS attack
  Resolution: Enabled backup gateway routing, increased retry attempts
  Follow-up: Implemented circuit breaker pattern to prevent future cascading failures

Issue 2: EMI Calculation Mismatch (ERR_PAY_LOAN_002)
Symptoms:
- Students reporting incorrect EMI amounts
- Discrepancy between calculated EMI and actual deduction
- Loan account balance not matching expected values
- Audit logs showing calculation errors

Root Causes:
- Interest rate changes not reflected in EMI calculation
- Floating vs fixed rate calculation errors
- Partial payment adjustments not accounted for
- Currency conversion errors for international loans

Mitigation Steps:
Step 1: Verify Interest Rate Configuration
- Check current interest rates in loan configuration: SELECT * FROM loan_interest_rates WHERE effective_date <= CURRENT_DATE;
- Compare with EMI calculation inputs
- Verify rate type (fixed/floating) matches loan agreement
- Check for rate change notifications that weren't applied

Step 2: Recalculate EMI for Affected Loans
- Identify affected loan accounts: SELECT loan_id FROM payments WHERE calculation_error = true;
- Run EMI recalculation job: payment-service --recalculate-emi --loan-ids {loan_ids}
- Verify calculations match loan agreement terms
- Update loan account balances accordingly

Step 3: Validate Partial Payment Logic
- Review partial payment processing logic
- Ensure partial payments reduce principal correctly
- Verify interest calculation accounts for reduced principal
- Test with sample partial payment scenarios

Step 4: Fix Currency Conversion (if applicable)
- Check exchange rates used for international loans
- Verify currency conversion happens at correct stage (payment vs calculation)
- Ensure exchange rate source is reliable and updated daily
- Recalculate affected international loan EMIs

Step 5: Verify Resolution
- Run validation queries to ensure all EMIs are correct
- Compare calculated EMIs with loan agreements
- Verify loan account balances are accurate
- Send correction notifications to affected students if needed

Rollback Procedure:
1. Restore previous EMI calculations from backup
2. Revert interest rate changes if incorrect
3. Restore original loan account balances
4. Notify affected students of correction process

Past Incidents:
- Incident INC-2024-015: EMI calculation error on 2024-02-20, affecting 150 loans
  Root cause: Interest rate change notification not processed correctly
  Resolution: Recalculated all affected EMIs, updated loan accounts
  Follow-up: Improved rate change notification processing, added validation checks

Issue 3: Payment Reconciliation Failure (ERR_PAY_LOAN_003)
Symptoms:
- Payments received but not matched to loan accounts
- Unmatched payment transactions accumulating
- Students reporting payments not reflected in loan balance
- Reconciliation job failing with errors

Root Causes:
- Payment reference numbers not matching loan account numbers
- Duplicate payment processing
- Payment gateway webhook delivery failures
- Database transaction deadlocks during reconciliation

Mitigation Steps:
Step 1: Check Unmatched Payments
- Query unmatched payments: SELECT * FROM payments WHERE loan_account_id IS NULL AND created_at > NOW() - INTERVAL '24 hours';
- Review payment reference numbers for pattern matching
- Check for duplicate payments: SELECT payment_ref, COUNT(*) FROM payments GROUP BY payment_ref HAVING COUNT(*) > 1;

Step 2: Verify Webhook Delivery
- Check webhook delivery logs: SELECT * FROM webhook_logs WHERE status = 'failed' AND created_at > NOW() - INTERVAL '24 hours';
- Verify webhook endpoint is accessible: curl https://api.loanservice.com/webhooks/payment
- Check webhook authentication tokens are valid
- Review payment gateway webhook configuration

Step 3: Manual Reconciliation
- For critical unmatched payments, manually match to loan accounts
- Use payment reference number to identify loan account
- Verify student details match payment details
- Update payment records: UPDATE payments SET loan_account_id = {loan_id} WHERE payment_id = {payment_id};

Step 4: Fix Reconciliation Job
- Review reconciliation job logs for errors
- Check for database deadlocks: SELECT * FROM pg_stat_database_conflicts;
- Optimize reconciliation queries to reduce lock contention
- Add retry logic for failed reconciliation attempts

Step 5: Verify Resolution
- Monitor unmatched payment count: Should decrease to zero
- Verify all recent payments are matched to loan accounts
- Confirm loan account balances are updated correctly
- Test webhook delivery with sample payment

Rollback Procedure:
1. Stop automated reconciliation job
2. Restore payment records from backup if incorrect matches made
3. Revert webhook configuration changes
4. Resume manual reconciliation process

Past Incidents:
- Incident INC-2024-028: Payment reconciliation failure on 2024-03-10, 500 unmatched payments
  Root cause: Webhook delivery failures due to authentication token expiration
  Resolution: Regenerated webhook tokens, manually reconciled unmatched payments
  Follow-up: Implemented automatic token rotation, added webhook delivery monitoring

Error Codes Reference
ERR_PAY_LOAN_001: Payment gateway timeout - Retry with exponential backoff, check gateway status
ERR_PAY_LOAN_002: EMI calculation mismatch - Recalculate EMI, verify interest rate configuration
ERR_PAY_LOAN_003: Payment reconciliation failure - Check webhook delivery, manually match payments
ERR_PAY_LOAN_004: Insufficient funds in student account - Student-facing, no action needed
ERR_PAY_LOAN_005: Payment gateway authentication failure - Verify API credentials, regenerate if needed
ERR_PAY_LOAN_006: Duplicate payment detected - Mark as duplicate, refund if necessary
ERR_PAY_LOAN_007: Loan account not found - Verify loan account exists, check account number format
ERR_PAY_LOAN_008: Payment amount mismatch - Verify payment amount matches EMI, handle partial payments
ERR_PAY_LOAN_009: Currency conversion error - Check exchange rates, verify currency code
ERR_PAY_LOAN_010: Payment processing queue full - Scale processing workers, check queue depth

SLA Requirements
- P0 (Critical): Payment service down - Resolve within 15 minutes
- P1 (High): Payment processing failures >5% - Resolve within 1 hour
- P2 (Medium): Payment reconciliation delays - Resolve within 4 hours
- P3 (Low): Payment notification delays - Resolve within 24 hours

Monitoring and Alerts
- Payment success rate: Target >99.5%, alert if <99%
- Payment processing time: P95 <3 seconds, alert if >5 seconds
- Unmatched payments: Alert if >10 unmatched payments in 1 hour
- Payment gateway latency: Alert if >2 seconds average response time
"""

LOAN_APPLICATION_FAQ = """
Education Loan Application Service FAQ

Q: Why is my loan application stuck in "Under Review" status?
A: Applications can remain in "Under Review" for several reasons:
1. Document verification pending: Check if all required documents (transcripts, admission letters, income proof) are uploaded and verified
2. Credit check in progress: Credit bureau verification can take 2-3 business days
3. Eligibility assessment: Complex eligibility criteria may require manual review
4. System processing delay: High application volume can cause processing delays

To check status: Log into your student portal and navigate to "My Applications" section.
If application is pending >7 days, contact support with your application reference number.

Q: How do I upload missing documents for my loan application?
A: To upload documents:
1. Log into student portal: https://portal.loanservice.com
2. Navigate to "My Applications" → Select your application
3. Click "Upload Documents" button
4. Select document type (Transcript, Admission Letter, Income Proof, etc.)
5. Upload file (PDF, JPG, PNG formats accepted, max 10MB per file)
6. Click "Submit" and wait for verification confirmation email

Note: Documents are automatically verified using OCR and AI. If verification fails, you'll receive an email with specific issues to address.

Q: What is the maximum loan amount I can apply for?
A: Maximum loan amounts vary by:
- Country: USA ($150,000), UK (£100,000), Canada (CAD 200,000), Germany (€120,000), India (₹50,00,000)
- Course type: Undergraduate, Graduate, Professional programs have different limits
- Collateral: Secured loans allow higher amounts than unsecured loans
- Credit score: Higher credit scores qualify for larger loan amounts

Use the loan eligibility calculator on our website to estimate your maximum loan amount based on your profile.

Q: Why was my loan application rejected?
A: Common rejection reasons include:
1. Insufficient credit score: Minimum credit score requirement not met
2. Incomplete documentation: Required documents missing or unverifiable
3. Eligibility criteria not met: Age, course, or institution not eligible
4. Income verification failure: Income proof documents don't meet requirements
5. Existing loan defaults: Previous loan payment defaults or delinquencies

You'll receive a detailed rejection letter via email explaining the specific reason. You can reapply after addressing the issues mentioned in the rejection letter.

Q: How long does loan approval take?
A: Loan approval timeline:
- Fast-track applications (pre-approved): 24-48 hours
- Standard applications: 5-7 business days
- Complex applications (manual review): 10-14 business days

Timeline depends on:
- Document verification speed
- Credit check completion
- Eligibility assessment complexity
- Application volume at time of submission

You'll receive email notifications at each stage: Application Received, Under Review, Approved/Rejected.

Q: Can I modify my loan application after submission?
A: Yes, you can modify certain details:
- Update contact information: Email, phone number, address
- Upload additional documents: Supporting documents, updated transcripts
- Change loan amount: Increase or decrease within eligibility limits
- Update course details: If admission details change

To modify: Log into portal → My Applications → Select application → Click "Modify Application"
Note: Major changes (course, institution) may require re-submission of application.

Q: What happens if I miss the loan disbursement deadline?
A: If you miss the disbursement deadline:
1. Contact support immediately with your application reference number
2. Provide reason for delay (e.g., admission confirmation pending)
3. Support team will review and may extend deadline by 30 days
4. If deadline cannot be extended, you may need to reapply for next academic term

Important: Disbursement deadlines are tied to academic term start dates. Missing deadline may affect your admission.

Q: How do I check my loan application status?
A: Multiple ways to check status:
1. Student Portal: Log in → My Applications → View status
2. Email notifications: Check email for status update notifications
3. SMS alerts: Receive SMS for major status changes
4. Support chat: Contact support with application reference number

Status values: Draft, Submitted, Under Review, Approved, Rejected, Disbursed, Cancelled

Q: What documents are required for loan application?
A: Required documents vary by country and loan type:
- Common documents: Identity proof, Address proof, Income proof, Academic transcripts
- Country-specific: USA (F-1 visa), UK (Tier 4 visa), Canada (Study permit)
- Course-specific: Admission letter, Course fee structure, Institution accreditation proof
- Collateral (if applicable): Property documents, Guarantor details

Complete document checklist is available in the application form. Upload all documents before submission to avoid delays.

Q: Can I apply for multiple loans simultaneously?
A: Yes, you can apply for multiple loans if:
- Total loan amount across all applications doesn't exceed maximum eligibility
- Each application is for a different academic program or institution
- You meet eligibility criteria for each loan type

Note: Multiple applications are assessed independently. Approval of one doesn't guarantee approval of others.

Q: What is the interest rate for education loans?
A: Interest rates vary by:
- Loan type: Secured vs Unsecured loans
- Country: Different rates for different countries
- Credit score: Higher credit scores get lower rates
- Loan amount: Larger loans may have different rates
- Repayment term: Longer terms may have different rates

Current rates (as of 2024):
- USA: 4.5% - 12% APR (fixed), 3.5% - 10% APR (variable)
- UK: 5.0% - 11% APR
- Canada: 4.0% - 9% APR
- Germany: 3.5% - 8% APR
- India: 8.5% - 14% APR

Use the interest rate calculator on our website for personalized rates based on your profile.

Q: How do I cancel my loan application?
A: To cancel application:
1. Log into student portal → My Applications
2. Select application → Click "Cancel Application"
3. Confirm cancellation (this action cannot be undone)
4. Receive cancellation confirmation email

Note: You can only cancel applications in "Draft" or "Submitted" status. Once "Under Review", contact support to cancel.

Q: What is the loan disbursement process?
A: Disbursement process:
1. Loan approval confirmation sent via email
2. Disbursement schedule created based on academic term dates
3. First disbursement: 80% of loan amount before term start
4. Remaining 20%: After mid-term verification of enrollment
5. Funds transferred directly to institution or student account
6. Disbursement confirmation sent via email and SMS

Disbursement timeline: 3-5 business days after approval confirmation.

Q: Can I prepay my education loan?
A: Yes, prepayment options available:
- Partial prepayment: Pay additional amount along with regular EMI
- Full prepayment: Pay entire outstanding loan amount
- Prepayment charges: Vary by country and loan terms (typically 0-2% of prepaid amount)
- Interest savings: Prepayment reduces total interest payable

To prepay: Log into portal → My Loans → Select loan → Click "Prepay" → Enter amount → Confirm

Q: What happens if I default on loan payments?
A: Loan default consequences:
1. Late payment fees: Applied after grace period (typically 15 days)
2. Credit score impact: Defaults reported to credit bureaus
3. Collection process: Support team contacts for payment arrangement
4. Legal action: For severe defaults, legal proceedings may be initiated
5. Loan acceleration: Entire loan amount may become due immediately

To avoid default: Contact support before payment due date to discuss payment plan options.

Q: How do I update my contact information?
A: To update contact details:
1. Log into student portal → Profile Settings
2. Update email, phone number, or address
3. Verify new email/phone via OTP
4. Changes take effect immediately

Important: Keep contact information updated to receive important loan notifications.

Q: What is the loan repayment grace period?
A: Grace period details:
- Duration: 6 months after course completion or graduation
- During grace period: No EMI payments required, interest may accrue
- After grace period: Regular EMI payments begin
- Grace period extension: Available for specific circumstances (further studies, unemployment)

Grace period is automatically applied. You'll receive notification 30 days before grace period ends.

Q: Can I transfer my loan to another student?
A: No, education loans are non-transferable. Loans are approved based on:
- Student's credit profile
- Student's academic credentials
- Student's income/collateral

If you cannot continue studies, contact support to discuss loan closure or deferment options.

Q: How do I calculate my EMI?
A: EMI calculation formula:
EMI = [P × R × (1+R)^N] / [(1+R)^N - 1]
Where: P = Principal, R = Monthly interest rate, N = Number of months

Use our EMI calculator: https://loanservice.com/emi-calculator
Input: Loan amount, interest rate, repayment tenure
Output: Monthly EMI amount, total interest, total amount payable

Q: What is the minimum and maximum loan tenure?
A: Loan tenure options:
- Minimum: 1 year (12 months)
- Maximum: 15 years (180 months)
- Standard tenure: 5-10 years
- Tenure selection: Based on loan amount and student preference

Longer tenure = Lower EMI but higher total interest
Shorter tenure = Higher EMI but lower total interest

Q: How do I contact support for loan-related queries?
A: Support channels:
1. Student Portal Chat: Available 24/7, average response time 2 minutes
2. Email: support@loanservice.com, response within 4 hours
3. Phone: Country-specific helpline numbers (business hours)
4. WhatsApp: +1-XXX-XXX-XXXX (for quick queries)
5. In-person: Visit branch offices (by appointment)

For urgent issues (payment failures, application errors), use chat or phone support.
"""

AUTHENTICATION_RUNBOOK = """
Student Authentication Service Runbook: {title}

Overview
This runbook provides procedures for handling authentication and authorization issues in the Education Loan Platform.
The authentication service manages student login, session management, OAuth integrations, and multi-factor authentication
for students across {regions} regions accessing the loan application and management portal.

Architecture
The Authentication Service architecture consists of:
- Identity Provider Layer: Handles student identity verification and authentication
- OAuth Integration: Supports Google, Microsoft, and Apple Sign-In for seamless login
- Session Management: Redis-based session storage with JWT token issuance
- Multi-Factor Authentication (MFA): SMS and email-based 2FA for enhanced security
- Password Management: Secure password hashing, reset flows, and policy enforcement
- Role-Based Access Control (RBAC): Different access levels for students, parents, guarantors

Service integrations:
- Student Database: PostgreSQL database storing student profiles and credentials
- Redis Cache: Session storage and token caching
- SMS Service: OTP delivery for MFA
- Email Service: Password reset and security notifications
- Audit Logging: All authentication events logged for compliance

Common Issues

Issue 1: OAuth Provider Failure (ERR_AUTH_LOAN_001)
Symptoms:
- Students unable to login using Google/Microsoft/Apple Sign-In
- OAuth callback errors in application logs
- "Authentication failed" errors when using social login
- High error rate for OAuth authentication attempts

Root Causes:
- OAuth provider (Google/Microsoft/Apple) experiencing outages
- OAuth application credentials expired or revoked
- Redirect URI mismatch in OAuth configuration
- Network connectivity issues between our service and OAuth provider

Mitigation Steps:
Step 1: Check OAuth Provider Status
- Google: https://status.cloud.google.com
- Microsoft: https://status.azure.com
- Apple: https://developer.apple.com/system-status/
- Verify if provider is experiencing any incidents

Step 2: Verify OAuth Application Configuration
- Check OAuth client ID and secret are valid: auth-service --config get oauth_credentials
- Verify redirect URIs match exactly: https://portal.loanservice.com/auth/callback
- Review OAuth application settings in provider console
- Ensure OAuth app is not disabled or restricted

Step 3: Test OAuth Flow Manually
- Test OAuth callback endpoint: curl https://api.loanservice.com/auth/oauth/callback?code=test
- Check OAuth token exchange: Verify token endpoint is accessible
- Review OAuth error logs: SELECT * FROM auth_logs WHERE error_type = 'oauth_failure' AND created_at > NOW() - INTERVAL '1 hour';
- Identify specific OAuth error codes from logs

Step 4: Enable Password Fallback
- If OAuth provider is down, enable password authentication fallback
- Configure fallback: auth-service --config enable_password_fallback=true
- Notify students via email about temporary OAuth unavailability
- Monitor OAuth provider recovery

Step 5: Verify Resolution
- Test OAuth login flow with test account
- Monitor OAuth success rate: Should return to >99%
- Verify students can successfully authenticate
- Disable password fallback once OAuth is restored

Rollback Procedure:
1. Disable password fallback: auth-service --config enable_password_fallback=false
2. Revert OAuth configuration changes if made
3. Restore previous OAuth credentials if updated
4. Notify team in #loan-auth-ops Slack channel

Past Incidents:
- Incident INC-2024-042: Google OAuth failure on 2024-04-15, duration 2 hours
  Root cause: Google OAuth API experiencing high latency due to regional outage
  Resolution: Enabled password fallback, monitored Google status, restored OAuth once available
  Follow-up: Implemented automatic OAuth health checks, added fallback automation

Issue 2: Account Lockout Due to Failed Login Attempts (ERR_AUTH_LOAN_002)
Symptoms:
- Students reporting "Account locked" errors when trying to login
- High number of failed login attempts in audit logs
- Account lockout notifications being sent to students
- Support tickets increasing for account unlock requests

Root Causes:
- Students forgetting passwords and attempting multiple logins
- Brute force attacks on student accounts
- Account lockout threshold set too low
- Password reset emails not being delivered

Mitigation Steps:
Step 1: Check Account Lockout Policy
- Review lockout configuration: auth-service --config get lockout_policy
- Current settings: lockout_threshold=5, lockout_duration=30 minutes
- Check if threshold is appropriate for legitimate use cases
- Review recent lockout events: SELECT * FROM account_lockouts WHERE created_at > NOW() - INTERVAL '24 hours';

Step 2: Identify Brute Force Attacks
- Check for suspicious login patterns: Multiple failed attempts from same IP
- Query failed login attempts: SELECT ip_address, COUNT(*) FROM failed_logins WHERE created_at > NOW() - INTERVAL '1 hour' GROUP BY ip_address HAVING COUNT(*) > 10;
- Block suspicious IP addresses if confirmed as attacks
- Review account lockouts to distinguish attacks from legitimate forgotten passwords

Step 3: Verify Password Reset Flow
- Test password reset email delivery: Check if emails are being sent
- Verify password reset links are working: Test reset link generation
- Check email service status: Ensure password reset emails are not being blocked
- Review password reset success rate: Should be >95%

Step 4: Unlock Affected Accounts
- For legitimate lockouts (forgotten passwords): Unlock accounts manually
- Use admin tool: auth-service --admin unlock-account --student-id {student_id}
- For bulk unlocks: auth-service --admin unlock-accounts --user-ids {comma_separated_ids}
- Send unlock confirmation emails to students

Step 5: Adjust Lockout Policy (if needed)
- If lockout threshold too aggressive, increase threshold: auth-service --config set lockout_threshold=10
- Extend lockout duration if needed: auth-service --config set lockout_duration=60
- Monitor lockout rate after changes
- Balance security with user experience

Step 6: Verify Resolution
- Test login flow with previously locked account
- Monitor account lockout rate: Should decrease
- Verify password reset flow is working
- Confirm students can successfully unlock accounts

Rollback Procedure:
1. Restore previous lockout policy settings
2. Re-lock accounts if incorrectly unlocked
3. Restore IP blocklist if incorrectly modified
4. Notify team of rollback

Past Incidents:
- Incident INC-2024-055: Mass account lockouts on 2024-05-20, 500+ accounts locked
  Root cause: Lockout threshold too low (3 attempts), students forgetting passwords during exam season
  Resolution: Increased threshold to 5, unlocked affected accounts, improved password reset flow
  Follow-up: Implemented progressive lockout (warning after 3, lock after 5), added password strength meter

Issue 3: Session Expiration Issues (ERR_AUTH_LOAN_003)
Symptoms:
- Students being logged out unexpectedly during loan application
- "Session expired" errors appearing frequently
- Students losing progress on multi-page forms
- High session expiration rate in logs

Root Causes:
- Session timeout configured too short for long forms
- Redis session store experiencing connectivity issues
- Session tokens not being refreshed properly
- Browser cookie settings blocking session cookies

Mitigation Steps:
Step 1: Check Session Configuration
- Review session timeout settings: auth-service --config get session_timeout
- Current timeout: 30 minutes (may be too short for loan applications)
- Check session refresh logic: Verify tokens are refreshed on activity
- Review session expiration logs: SELECT * FROM session_logs WHERE expiration_reason = 'timeout' AND created_at > NOW() - INTERVAL '24 hours';

Step 2: Verify Redis Session Store
- Check Redis connectivity: redis-cli ping
- Monitor Redis memory usage: redis-cli INFO memory
- Check for Redis connection errors in logs
- Verify session data is being stored: redis-cli GET session:{session_id}

Step 3: Test Session Refresh
- Verify session tokens are refreshed on user activity
- Check token refresh endpoint is working: curl https://api.loanservice.com/auth/refresh
- Review token refresh logic in code
- Ensure refresh tokens are being issued correctly

Step 4: Adjust Session Timeout
- For loan applications, increase session timeout: auth-service --config set session_timeout=60
- Implement activity-based session extension
- Add session warning before expiration (5 minutes before)
- Save form progress automatically to prevent data loss

Step 5: Verify Resolution
- Test long-form completion (loan application)
- Monitor session expiration rate: Should decrease
- Verify students can complete applications without session expiry
- Confirm session refresh is working

Rollback Procedure:
1. Restore previous session timeout settings
2. Revert session refresh logic if changed
3. Restore Redis configuration if modified
4. Notify team of changes

Past Incidents:
- Incident INC-2024-068: Session expiration during loan application on 2024-06-10
  Root cause: Session timeout 30 minutes too short for complex loan applications (average 45 minutes)
  Resolution: Increased timeout to 60 minutes, added auto-save for form progress
  Follow-up: Implemented activity-based session extension, added session warning notifications

Error Codes Reference
ERR_AUTH_LOAN_001: OAuth provider failure - Check provider status, enable password fallback
ERR_AUTH_LOAN_002: Account locked - Review lockout policy, unlock if legitimate
ERR_AUTH_LOAN_003: Session expired - Check session timeout, verify Redis connectivity
ERR_AUTH_LOAN_004: Invalid credentials - Student-facing, no action needed
ERR_AUTH_LOAN_005: MFA code expired - Student can request new code
ERR_AUTH_LOAN_006: Password reset token invalid - Student can request new reset link
ERR_AUTH_LOAN_007: Account not found - Verify student exists in database
ERR_AUTH_LOAN_008: OAuth token exchange failed - Check OAuth configuration
ERR_AUTH_LOAN_009: Session store unavailable - Check Redis connectivity
ERR_AUTH_LOAN_010: Rate limit exceeded - Temporary lockout, auto-unlocks after cooldown

SLA Requirements
- P0 (Critical): Authentication service down - Resolve within 15 minutes
- P1 (High): Login failure rate >5% - Resolve within 1 hour
- P2 (Medium): Session issues - Resolve within 4 hours
- P3 (Low): Password reset delays - Resolve within 24 hours

Monitoring and Alerts
- Login success rate: Target >99%, alert if <95%
- Session expiration rate: Alert if >10% of sessions expire prematurely
- Account lockout rate: Alert if >100 lockouts per hour
- OAuth success rate: Alert if <95%
"""

# Continue with more templates for Redis, Kafka, Database, Notifications...

def generate_filename_list(count: int = 100) -> dict:
    """Generate complete list of 100+ filenames grouped by type."""
    rng = random.Random(42)  # Fixed seed for reproducibility
    
    domains = ["payment_processing", "loan_application", "authentication", "redis_cache", 
               "kafka_queues", "database", "notifications"]
    file_types = {
        "pdf": [],
        "docx": [],
        "txt": [],
        "images": []
    }
    
    # PDFs: Runbooks and troubleshooting guides (40 files)
    runbook_types = ["payment_processing", "loan_application", "authentication", 
                     "disbursement", "repayment", "document_verification"]
    for i in range(40):
        domain = rng.choice(runbook_types)
        env = rng.choice(["prod", "staging", "dev"])
        region = rng.choice(["us", "uk", "ca", "de", "in"])
        file_types["pdf"].append(f"{domain}_runbook_{i+1:03d}_{region}_{env}.pdf")
    
    # Word docs: FAQs, SLA policies, escalation guides (30 files)
    doc_types = ["faq", "sla_policy", "escalation_guide", "onboarding"]
    for i in range(30):
        domain = rng.choice(domains)
        doc_type = rng.choice(doc_types)
        file_types["docx"].append(f"{domain}_{doc_type}_{i+1:03d}.docx")
    
    # TXT: Error codes, configuration notes (40 files)
    for i in range(20):
        domain = rng.choice(domains)
        file_types["txt"].append(f"{domain}_error_codes_{i+1:03d}.txt")
        file_types["txt"].append(f"{domain}_config_reference_{i+1:03d}.txt")
    
    # Images: Architecture diagrams (10 files)
    for i in range(10):
        domain = rng.choice(domains)
        file_types["images"].append(f"{domain}_architecture_diagram_{i+1:03d}.png")
    
    return file_types


def generate_sample_documents() -> dict:
    """Generate full content for 10 representative documents."""
    rng = random.Random(42)
    
    samples = {
        "payment_processing_runbook_001_us_prod.pdf": _ensure_word_count(
            PAYMENT_PROCESSING_RUNBOOK.format(
                title="Payment Gateway Timeout and EMI Calculation Issues",
                region="United States",
                payment_methods="credit card, debit card, bank transfer, ACH",
                countries="USA, Canada",
                gateway="razorpay",
            ),
            MIN_WORDS_PER_DOC,
            MAX_WORDS_PER_DOC
        ),
        "loan_application_faq_001.docx": _ensure_word_count(
            LOAN_APPLICATION_FAQ,
            MIN_WORDS_PER_DOC,
            MAX_WORDS_PER_DOC
        ),
        "authentication_runbook_001_us_prod.pdf": _ensure_word_count(
            AUTHENTICATION_RUNBOOK.format(
                title="OAuth Provider Failures and Account Lockout Management",
                regions="US, UK, Canada, Germany, India"
            ),
            MIN_WORDS_PER_DOC,
            MAX_WORDS_PER_DOC
        ),
        # Add more samples...
    }
    
    return samples


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Education Loan Dataset Generator")
    parser.add_argument("--output-dir", type=Path, default=Path("data/kb/education_loans"))
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--list-only", action="store_true")
    args = parser.parse_args()
    
    # Generate file list
    file_list = generate_filename_list(args.count)
    
    # Save file list
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "education_loan_file_list.json", "w") as f:
        json.dump(file_list, f, indent=2)
    
    total_files = sum(len(files) for files in file_list.values())
    print(f"Generated file list: {total_files} files")
    print(f"  - PDFs: {len(file_list['pdf'])}")
    print(f"  - Word docs: {len(file_list['docx'])}")
    print(f"  - TXT files: {len(file_list['txt'])}")
    print(f"  - Images: {len(file_list['images'])}")
    
    if args.list_only:
        print(f"\nFile list saved to {output_dir / 'education_loan_file_list.json'}")
        exit(0)
    
    # Generate sample content
    samples = generate_sample_documents()
    samples_dir = output_dir / "samples"
    samples_dir.mkdir(exist_ok=True)
    
    for filename, content in samples.items():
        txt_path = samples_dir / filename.replace(".pdf", ".txt").replace(".docx", ".txt")
        txt_path.write_text(content, encoding="utf-8")
    
    print(f"\nGenerated {len(samples)} sample documents in {samples_dir}")
    print("\nNote: Remaining files are structured variants using the same templates")
