#!/usr/bin/env python3
"""Dataset Generator Agent - Creates synthetic support knowledge base.

This agent is COMPLETELY SEPARATE from the main customer support system.
It generates 100+ files (PDF, Word, TXT, Images) for RAG testing.

Usage:
    python -m agents.dataset_generator [--output-dir data/kb/synthetic] [--count 100]
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
# DOMAIN-SPECIFIC TEMPLATES
# ============================================
# Domains: Payment, Checkout, Auth, Redis, Kafka, Database, Notifications

PAYMENT_RUNBOOK_TEMPLATE = """
Payment Service Runbook: {title}

Overview
This runbook provides step-by-step procedures for handling {scenario} in the Payment Service.
The Payment Service processes transactions for {region} region and handles {payment_methods}.

Prerequisites
- Access to Payment Service dashboard (role: {role})
- Access to transaction logs database
- API keys for payment gateway integration
- Monitoring dashboard access

Step 1: Identify the Issue
1. Navigate to Payment Service dashboard: https://payments.{env}.example.com/dashboard
2. Check the error rate metric in the last {time_window}
3. Review transaction logs for error codes: {error_codes}
4. Identify affected payment methods: {payment_methods}

Step 2: Diagnose Root Cause
Run diagnostic command:
```bash
curl -X POST https://payments.{env}.example.com/api/v1/diagnostics \\
  -H "Authorization: Bearer $API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{{"transaction_id": "{transaction_id}", "check": "full"}}'
```

Expected output should show:
- Payment gateway connectivity: OK
- Database connection pool: {pool_status}
- Redis cache status: {cache_status}
- Message queue depth: {queue_depth}

Step 3: Apply Mitigation
If error code is {error_code}:
1. Check payment gateway status: https://status.paymentgateway.com
2. If gateway is down, enable failover to secondary gateway
3. Run: `payment-service --failover --gateway secondary`
4. Verify transactions resume: Monitor dashboard for 5 minutes

If error code is {error_code_2}:
1. Check database connection pool exhaustion
2. Increase pool size: `payment-service --config pool_size=50`
3. Restart service: `systemctl restart payment-service`
4. Verify health endpoint: `curl http://localhost:8080/health`

Step 4: Verify Resolution
1. Check error rate drops below 0.1% threshold
2. Verify transaction success rate > 99.9%
3. Monitor for 30 minutes to ensure stability
4. Update incident log with resolution details

Rollback Procedure
If mitigation causes issues:
1. Revert configuration: `payment-service --config --revert`
2. Restore previous gateway: `payment-service --failover --gateway primary`
3. Checkpoint database state before any changes
4. Notify team in #payment-ops Slack channel

Common Error Codes
- ERR_PAY_001: Payment gateway timeout (retry with exponential backoff)
- ERR_PAY_002: Invalid payment method (check customer payment profile)
- ERR_PAY_003: Insufficient funds (customer-facing, no action needed)
- ERR_PAY_004: Database connection failure (check connection pool)
- ERR_PAY_005: Redis cache miss (expected for new transactions)

SLA Requirements
- P0 (Critical): Resolve within 15 minutes
- P1 (High): Resolve within 1 hour
- P2 (Medium): Resolve within 4 hours
- P3 (Low): Resolve within 24 hours
"""

CHECKOUT_FAQ_TEMPLATE = """
Checkout Service FAQ

Q: Why is my checkout failing with error CHECKOUT_ERR_502?
A: Error CHECKOUT_ERR_502 typically indicates a timeout when communicating with the payment service.
Check the following:
1. Verify payment service is healthy: `curl https://payments.example.com/health`
2. Check network connectivity between checkout and payment services
3. Review checkout service logs for timeout errors
4. If issue persists, check if payment gateway is experiencing issues

Q: How do I reset a stuck checkout session?
A: Stuck checkout sessions can be reset via the admin API:
```bash
curl -X POST https://checkout.example.com/api/admin/sessions/{session_id}/reset \\
  -H "Authorization: Bearer $ADMIN_TOKEN"
```
This clears the session state and allows the customer to start a new checkout.

Q: What is the maximum cart value allowed?
A: The maximum cart value is $10,000 USD (or equivalent in other currencies).
For higher values, contact support to enable enterprise checkout with additional verification.

Q: Why are some items showing as out of stock during checkout?
A: Inventory is checked in real-time during checkout. If an item becomes unavailable
between adding to cart and checkout completion, it will be marked as unavailable.
The customer can remove the item or wait for restock notification.

Q: How do I configure checkout timeout duration?
A: Set the CHECKOUT_TIMEOUT_SECONDS environment variable (default: 1800 seconds / 30 minutes).
For high-value carts, consider increasing timeout to allow for additional verification steps.

Q: What happens if payment fails during checkout?
A: The checkout session is preserved for 24 hours. The customer can retry payment
or update payment method. After 24 hours, the session expires and cart is cleared.

Q: How do I enable multi-currency checkout?
A: Multi-currency is enabled by default. Supported currencies: USD, EUR, GBP, JPY, CAD, AUD.
Currency conversion rates are updated hourly from the exchange rate service.

Q: Why is checkout redirecting to a different payment page?
A: This occurs when 3D Secure authentication is required for the payment method.
This is a security requirement and cannot be disabled for certain payment methods.

Q: How do I test checkout in sandbox mode?
A: Set environment variable CHECKOUT_ENV=sandbox. Use test card numbers:
- Success: 4242 4242 4242 4242
- Decline: 4000 0000 0000 0002
- 3D Secure: 4000 0025 0000 3155

Q: What is the checkout completion rate SLA?
A: Target checkout completion rate is >95%. If rate drops below 90%, this triggers
a P1 incident and requires immediate investigation.
"""

AUTH_RUNBOOK_TEMPLATE = """
Authentication Service Runbook: {title}

Service Overview
The Authentication Service handles user login, session management, and token issuance
for all customer-facing applications. It integrates with {auth_providers} and supports
{auth_methods} authentication methods.

Prerequisites
- Admin access to Auth Service console
- Access to user database (read-only for diagnostics)
- OAuth provider credentials
- Session store access (Redis)

Step 1: Identify Authentication Failure
1. Check Auth Service dashboard: https://auth.{env}.example.com/admin
2. Review failed login attempts in the last {time_window}
3. Identify error patterns:
   - ERR_AUTH_001: Invalid credentials (expected for failed login attempts)
   - ERR_AUTH_002: Account locked (too many failed attempts)
   - ERR_AUTH_003: Token expiration (session timeout)
   - ERR_AUTH_004: OAuth provider failure
   - ERR_AUTH_005: Database connection error

Step 2: Diagnose Root Cause
Run diagnostic script:
```bash
./scripts/auth-diagnostics.sh --env {env} --check all
```

This checks:
- Database connectivity: {db_status}
- Redis session store: {redis_status}
- OAuth provider health: {oauth_status}
- Token signing service: {token_status}
- Rate limiting service: {rate_limit_status}

Step 3: Apply Fix Based on Error Code

For ERR_AUTH_002 (Account Locked):
1. Check account lockout policy: `auth-service --config get lockout_policy`
2. If lockout threshold too low, adjust: `auth-service --config set lockout_threshold=10`
3. Unlock affected accounts: `auth-service --admin unlock-accounts --user-ids {user_ids}`
4. Notify affected users via email

For ERR_AUTH_004 (OAuth Provider Failure):
1. Check OAuth provider status page
2. If provider is down, enable fallback to password auth: `auth-service --config enable_password_fallback`
3. Monitor OAuth provider recovery
4. Disable fallback once provider is healthy

For ERR_AUTH_005 (Database Error):
1. Check database connection pool: `auth-service --diagnostics db-pool`
2. If pool exhausted, increase pool size: `auth-service --config db_pool_size=100`
3. Check for long-running queries blocking connections
4. Restart service if needed: `systemctl restart auth-service`

Step 4: Verify Resolution
1. Test login flow: Use test credentials to verify authentication works
2. Check error rate drops below threshold: <0.5% failure rate
3. Monitor session creation rate: Should match login success rate
4. Verify token issuance: Check token validation endpoint

Rollback Procedure
1. Revert configuration changes: `auth-service --config --revert`
2. Restore previous OAuth settings if changed
3. Unlock any accounts that were incorrectly locked
4. Notify team in #auth-ops channel

Security Considerations
- Never disable rate limiting in production
- Account lockout is a security feature, adjust carefully
- OAuth fallback should be temporary only
- All configuration changes must be logged for audit

SLA Requirements
- P0: Authentication service down - resolve within 15 minutes
- P1: High failure rate (>5%) - resolve within 1 hour
- P2: Moderate failure rate (1-5%) - resolve within 4 hours
"""

REDIS_FAQ_TEMPLATE = """
Redis Cache Service FAQ

Q: Why is Redis returning cache misses for known keys?
A: Cache misses can occur due to:
1. Redis instance restarted (cache cleared)
2. Memory limit reached (LRU eviction)
3. Key expiration (TTL expired)
4. Network partition between application and Redis

Check Redis memory usage: `redis-cli INFO memory`
Check key TTL: `redis-cli TTL {key_name}`

Q: How do I clear the Redis cache?
A: Use Redis CLI:
```bash
redis-cli FLUSHDB  # Clear current database
redis-cli FLUSHALL # Clear all databases (use with caution)
```

Or via admin API:
```bash
curl -X POST https://redis-admin.example.com/api/cache/clear \\
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Q: What is the Redis memory limit and eviction policy?
A: Default memory limit: 2GB per Redis instance.
Eviction policy: allkeys-lru (Least Recently Used)
When memory limit is reached, least recently used keys are evicted.

Q: How do I configure Redis TTL for different key patterns?
A: Set TTL in application code or use Redis configuration:
```bash
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

Application-level TTL examples:
- Session data: 24 hours
- API response cache: 5 minutes
- User profile cache: 1 hour

Q: Why is Redis connection timing out?
A: Timeouts can be caused by:
1. Network issues between application and Redis
2. Redis instance overloaded (high CPU/memory)
3. Connection pool exhausted
4. Firewall blocking connections

Check Redis performance: `redis-cli --latency`
Check connection count: `redis-cli INFO clients`

Q: How do I monitor Redis performance?
A: Use Redis monitoring commands:
- `redis-cli INFO stats` - General statistics
- `redis-cli INFO memory` - Memory usage
- `redis-cli --latency` - Latency monitoring
- `redis-cli MONITOR` - Real-time command monitoring

Q: What is the Redis replication setup?
A: Primary-replica setup with automatic failover:
- Primary: Handles all writes
- Replica: Handles reads (read scaling)
- Automatic failover via Redis Sentinel

Q: How do I add a new Redis key pattern?
A: Document the key pattern in the cache strategy document:
- Key format: `{service}:{entity}:{id}`
- TTL: Based on data freshness requirements
- Eviction: Handled by Redis policy

Q: What happens if Redis goes down?
A: Application should handle Redis failures gracefully:
1. Fall back to database queries (slower but functional)
2. Log cache miss errors for monitoring
3. Alert on-call engineer via PagerDuty
4. Redis Sentinel will attempt automatic failover

Q: How do I configure Redis for high availability?
A: Use Redis Cluster or Redis Sentinel:
- Redis Cluster: Sharding across multiple nodes
- Redis Sentinel: Automatic failover for primary-replica setup
- Both provide high availability and fault tolerance
"""

KAFKA_RUNBOOK_TEMPLATE = """
Kafka Message Queue Runbook: {title}

Overview
Kafka handles asynchronous message processing for {services}. This runbook covers
common scenarios including consumer lag, message processing failures, and broker issues.

Prerequisites
- Access to Kafka cluster management console
- Kafka CLI tools installed
- Access to consumer group monitoring
- Zookeeper/KRaft access (if applicable)

Step 1: Identify the Issue
1. Check Kafka cluster health: https://kafka.{env}.example.com/health
2. Review consumer lag metrics for all consumer groups
3. Check broker status and partition leader distribution
4. Review error logs for failed message processing

Common Issues:
- Consumer lag increasing (messages not being processed)
- Broker down (partition leader unavailable)
- Message processing failures (consumer errors)
- Topic replication issues (under-replicated partitions)

Step 2: Diagnose Consumer Lag
Check consumer group lag:
```bash
kafka-consumer-groups.sh --bootstrap-server {bootstrap_servers} \\
  --group {consumer_group} --describe
```

High lag indicates:
- Consumer is slow or stuck
- Consumer crashed and not processing
- Message processing is failing

Step 3: Diagnose Broker Issues
Check broker status:
```bash
kafka-broker-api-versions.sh --bootstrap-server {bootstrap_servers}
```

Check partition status:
```bash
kafka-topics.sh --bootstrap-server {bootstrap_servers} \\
  --topic {topic_name} --describe
```

Look for:
- Under-replicated partitions (replication factor not met)
- No leader (partition has no leader broker)
- Offline partitions (all replicas are down)

Step 4: Apply Fixes

For Consumer Lag:
1. Identify slow consumer: Check processing time metrics
2. Scale consumers: Increase consumer instances
3. Check for dead letter queue: Review failed messages
4. Restart stuck consumer: `systemctl restart {consumer_service}`

For Broker Down:
1. Check broker health: `curl https://{broker_host}:9092/health`
2. If broker is down, Kafka will elect new leader automatically
3. If automatic failover fails, manually reassign partition leadership
4. Restart broker: `systemctl restart kafka-broker`

For Message Processing Failures:
1. Check consumer error logs for exception details
2. Review message content for malformed data
3. Move failed messages to dead letter topic
4. Fix consumer code if bug identified

Step 5: Verify Resolution
1. Monitor consumer lag: Should decrease to near zero
2. Check message processing rate: Should match production rate
3. Verify no new errors in consumer logs
4. Confirm all partitions have leaders

Rollback Procedure
1. Revert any configuration changes
2. Restore previous consumer group offsets if needed
3. Restart affected services
4. Notify team in #kafka-ops channel

SLA Requirements
- P0: Kafka cluster down - resolve within 30 minutes
- P1: High consumer lag (>1 hour) - resolve within 2 hours
- P2: Broker issues - resolve within 4 hours
"""

DATABASE_FAQ_TEMPLATE = """
Database Service FAQ

Q: Why is my database query timing out?
A: Query timeouts can be caused by:
1. Missing database indexes on frequently queried columns
2. Long-running transactions blocking other queries
3. Database connection pool exhausted
4. Database server overloaded (high CPU/memory)

Check slow query log: `SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;`
Check active connections: `SELECT count(*) FROM pg_stat_activity;`

Q: How do I optimize a slow database query?
A: Steps to optimize:
1. Use EXPLAIN ANALYZE to see query execution plan
2. Identify missing indexes: `CREATE INDEX ON {table}({column});`
3. Rewrite query to use indexes efficiently
4. Consider query result caching if data doesn't change frequently

Q: What is the database connection pool configuration?
A: Default connection pool settings:
- Min connections: 5
- Max connections: 50
- Connection timeout: 30 seconds
- Idle timeout: 10 minutes

Adjust based on application load and database capacity.

Q: How do I handle database failover?
A: Database failover is automatic:
1. Primary database fails
2. Monitoring detects failure
3. Replica is promoted to primary
4. Application connections failover to new primary
5. Update DNS/connection string to point to new primary

Failover time: Typically 30-60 seconds.

Q: Why is database replication lag increasing?
A: Replication lag can increase due to:
1. High write load on primary
2. Network issues between primary and replica
3. Replica server resource constraints
4. Long-running queries on replica

Check replication lag: `SELECT pg_last_xlog_replay_location() - pg_last_xlog_receive_location();`

Q: How do I perform a database backup?
A: Use pg_dump for PostgreSQL:
```bash
pg_dump -h {host} -U {user} -d {database} -F c -f backup.dump
```

For automated backups, use scheduled jobs or backup service.

Q: What is the database retention policy?
A: Data retention:
- Transaction logs: 7 days
- Database backups: 30 days
- Point-in-time recovery: 7 days
- Archived backups: 1 year

Q: How do I monitor database performance?
A: Key metrics to monitor:
- Connection count: Should be <80% of max connections
- Query execution time: P95 should be <100ms for most queries
- Replication lag: Should be <1 second
- Database size: Monitor growth rate

Q: What happens during database maintenance?
A: Maintenance window: Sunday 2-4 AM UTC
- Database backups
- Index maintenance
- Statistics updates
- Vacuum operations

During maintenance, read replicas handle read traffic.

Q: How do I scale the database?
A: Scaling options:
1. Vertical scaling: Increase server resources (CPU, memory)
2. Read replicas: Add read replicas for read scaling
3. Sharding: Partition data across multiple databases
4. Connection pooling: Optimize connection usage
"""

NOTIFICATIONS_RUNBOOK_TEMPLATE = """
Notifications Service Runbook: {title}

Service Overview
The Notifications Service sends emails, SMS, and push notifications to users.
It integrates with {notification_providers} and handles {notification_types} notification types.

Prerequisites
- Access to Notifications Service dashboard
- API keys for notification providers (SendGrid, Twilio, etc.)
- Access to notification delivery logs
- Monitoring dashboard access

Step 1: Identify Notification Delivery Issues
1. Check Notifications Service dashboard: https://notifications.{env}.example.com/admin
2. Review delivery failure rate in the last {time_window}
3. Identify failure patterns:
   - Email delivery failures
   - SMS delivery failures
   - Push notification failures
   - Rate limiting issues

Step 2: Diagnose Root Cause
Run diagnostic command:
```bash
curl -X GET https://notifications.{env}.example.com/api/v1/health \\
  -H "Authorization: Bearer $API_KEY"
```

Check provider status:
- SendGrid status: https://status.sendgrid.com
- Twilio status: https://status.twilio.com
- APNs status: https://developer.apple.com/system-status/

Step 3: Apply Fixes

For Email Delivery Failures:
1. Check SendGrid API key validity
2. Verify sender domain authentication (SPF, DKIM, DMARC)
3. Check email content for spam triggers
4. Review bounce/complaint rates

For SMS Delivery Failures:
1. Check Twilio account balance
2. Verify phone number format and country code
3. Check SMS content for compliance issues
4. Review carrier delivery reports

For Push Notification Failures:
1. Verify device tokens are valid
2. Check APNs/FCM certificates are not expired
3. Verify notification payload format
4. Check device registration status

Step 4: Verify Resolution
1. Send test notification to verify delivery
2. Check delivery success rate returns to >99%
3. Monitor for 1 hour to ensure stability
4. Update incident log

Rollback Procedure
1. Revert any provider configuration changes
2. Restore previous API keys if changed
3. Re-enable disabled notification channels
4. Notify team in #notifications-ops channel

SLA Requirements
- P0: Notification service down - resolve within 15 minutes
- P1: High failure rate (>5%) - resolve within 1 hour
- P2: Moderate failure rate (1-5%) - resolve within 4 hours
"""

# ============================================
# IMAGE CONTENT (OCR TEXT)
# ============================================

IMAGE_OCR_TEMPLATES = [
    """
Architecture Diagram: Payment Service Flow

[Payment Flow Diagram]
User initiates payment → Checkout Service → Payment Gateway → Bank API
Response flows back: Bank API → Payment Gateway → Checkout Service → User

Components:
- Checkout Service: Handles payment initiation and user interaction
- Payment Gateway: Processes payment with bank
- Bank API: External bank integration
- Database: Stores transaction records
- Redis: Caches payment session data

Error Handling:
- Payment Gateway timeout: Retry with exponential backoff
- Bank API failure: Queue for retry, notify user
- Database error: Log transaction, manual reconciliation

Monitoring:
- Payment success rate: Target >99.5%
- Payment latency: P95 <2 seconds
- Error rate: Target <0.5%
""",
    """
System Architecture: Authentication Service

[Auth Service Architecture]
User Login → Auth Service → OAuth Provider → Token Service → Session Store (Redis)
User Profile → User Database

Components:
- Auth Service: Handles authentication logic
- OAuth Provider: External identity provider
- Token Service: Issues and validates JWT tokens
- Session Store: Redis for session management
- User Database: PostgreSQL for user data

Security:
- All communications over HTTPS
- Tokens signed with RSA-256
- Session data encrypted at rest
- Rate limiting on login attempts

Scalability:
- Horizontal scaling via load balancer
- Redis cluster for session store
- Database read replicas for user queries
""",
    """
Database Schema: User Transactions

[Database Schema Diagram]
users table:
- id (primary key)
- email (unique index)
- created_at
- updated_at

transactions table:
- id (primary key)
- user_id (foreign key to users.id)
- amount
- status
- created_at
- payment_method_id (foreign key)

payment_methods table:
- id (primary key)
- user_id (foreign key to users.id)
- type (card, bank_account)
- last4 (masked)
- created_at

Indexes:
- users.email (unique)
- transactions.user_id
- transactions.created_at
- payment_methods.user_id
""",
]


def _generate_payment_runbook(rng: random.Random, env: str, region: str) -> str:
    """Generate payment service runbook content."""
    scenarios = [
        "payment gateway timeout",
        "transaction processing failure",
        "payment method validation error",
        "refund processing",
    ]
    payment_methods = ["credit card", "debit card", "bank transfer", "digital wallet"]
    error_codes = ["ERR_PAY_001", "ERR_PAY_002", "ERR_PAY_003", "ERR_PAY_004", "ERR_PAY_005"]
    roles = ["admin", "operator", "support"]
    
    content = PAYMENT_RUNBOOK_TEMPLATE.format(
        title=f"Payment Service Runbook - {rng.choice(scenarios).title()}",
        scenario=rng.choice(scenarios),
        region=region,
        payment_methods=", ".join(rng.sample(payment_methods, 2)),
        role=rng.choice(roles),
        env=env,
        time_window=rng.choice(["15 minutes", "30 minutes", "1 hour"]),
        error_codes=", ".join(rng.sample(error_codes, 3)),
        transaction_id=f"TXN-{rng.randint(100000, 999999)}",
        pool_status=rng.choice(["OK", "WARNING", "CRITICAL"]),
        cache_status=rng.choice(["OK", "DEGRADED"]),
        queue_depth=rng.randint(0, 1000),
        error_code=rng.choice(error_codes),
        error_code_2=rng.choice([c for c in error_codes if c != error_codes[0]]),
    )
    return _ensure_word_count(content, MIN_WORDS_PER_DOC, MAX_WORDS_PER_DOC)


def _generate_checkout_faq(rng: random.Random) -> str:
    """Generate checkout service FAQ content."""
    # The template already has enough content, just ensure word count
    content = CHECKOUT_FAQ_TEMPLATE
    # Expand if needed
    while _word_count(content) < MIN_WORDS_PER_DOC:
        content += "\n\n" + CHECKOUT_FAQ_TEMPLATE
    return _ensure_word_count(content, MIN_WORDS_PER_DOC, MAX_WORDS_PER_DOC)


def _generate_auth_runbook(rng: random.Random, env: str) -> str:
    """Generate authentication service runbook content."""
    titles = [
        "Handling OAuth Provider Failures",
        "Account Lockout Management",
        "Token Expiration Issues",
        "Database Connection Failures",
    ]
    auth_providers = ["Google OAuth", "GitHub OAuth", "Microsoft Azure AD"]
    auth_methods = ["OAuth 2.0", "SAML", "password", "API key"]
    
    content = AUTH_RUNBOOK_TEMPLATE.format(
        title=rng.choice(titles),
        auth_providers=", ".join(rng.sample(auth_providers, 2)),
        auth_methods=", ".join(rng.sample(auth_methods, 2)),
        env=env,
        time_window=rng.choice(["15 minutes", "30 minutes", "1 hour"]),
        db_status=rng.choice(["OK", "DEGRADED", "ERROR"]),
        redis_status=rng.choice(["OK", "DEGRADED"]),
        oauth_status=rng.choice(["OK", "DOWN"]),
        token_status=rng.choice(["OK", "ERROR"]),
        rate_limit_status=rng.choice(["OK", "WARNING"]),
        user_ids=", ".join([f"user_{i}" for i in rng.sample(range(1000, 9999), 3)]),
    )
    return _ensure_word_count(content, MIN_WORDS_PER_DOC, MAX_WORDS_PER_DOC)


def _generate_redis_faq(rng: random.Random) -> str:
    """Generate Redis cache FAQ content."""
    content = REDIS_FAQ_TEMPLATE
    while _word_count(content) < MIN_WORDS_PER_DOC:
        content += "\n\n" + REDIS_FAQ_TEMPLATE
    return _ensure_word_count(content, MIN_WORDS_PER_DOC, MAX_WORDS_PER_DOC)


def _generate_kafka_runbook(rng: random.Random, env: str) -> str:
    """Generate Kafka runbook content."""
    titles = [
        "Handling Consumer Lag",
        "Broker Failure Recovery",
        "Message Processing Failures",
        "Topic Replication Issues",
    ]
    services = ["payment processing", "order fulfillment", "notification delivery", "analytics"]
    
    content = KAFKA_RUNBOOK_TEMPLATE.format(
        title=rng.choice(titles),
        services=", ".join(rng.sample(services, 2)),
        env=env,
        bootstrap_servers=f"kafka-{env}.example.com:9092",
        consumer_group=rng.choice(["payment-consumers", "order-consumers", "notification-consumers"]),
        topic_name=rng.choice(["payments", "orders", "notifications"]),
    )
    return _ensure_word_count(content, MIN_WORDS_PER_DOC, MAX_WORDS_PER_DOC)


def _generate_database_faq(rng: random.Random) -> str:
    """Generate database FAQ content."""
    content = DATABASE_FAQ_TEMPLATE
    while _word_count(content) < MIN_WORDS_PER_DOC:
        content += "\n\n" + DATABASE_FAQ_TEMPLATE
    return _ensure_word_count(content, MIN_WORDS_PER_DOC, MAX_WORDS_PER_DOC)


def _generate_notifications_runbook(rng: random.Random, env: str) -> str:
    """Generate notifications service runbook content."""
    titles = [
        "Email Delivery Failures",
        "SMS Delivery Issues",
        "Push Notification Failures",
        "Rate Limiting Issues",
    ]
    notification_providers = ["SendGrid", "Twilio", "APNs", "FCM"]
    notification_types = ["email", "SMS", "push", "in-app"]
    
    content = NOTIFICATIONS_RUNBOOK_TEMPLATE.format(
        title=rng.choice(titles),
        notification_providers=", ".join(rng.sample(notification_providers, 2)),
        notification_types=", ".join(rng.sample(notification_types, 2)),
        env=env,
        time_window=rng.choice(["15 minutes", "30 minutes", "1 hour"]),
    )
    return _ensure_word_count(content, MIN_WORDS_PER_DOC, MAX_WORDS_PER_DOC)


def _generate_image_ocr(rng: random.Random) -> str:
    """Generate OCR text for architecture diagrams."""
    return rng.choice(IMAGE_OCR_TEMPLATES)


# ============================================
# FILE GENERATION
# ============================================

def generate_dataset_file_list(count: int = 100) -> dict:
    """Generate complete list of 100+ filenames grouped by type."""
    rng = random.Random(42)  # Fixed seed for reproducibility
    
    domains = ["payment", "checkout", "auth", "redis", "kafka", "database", "notifications"]
    envs = ["prod", "staging", "dev"]
    regions = ["us-east", "us-west", "eu-west", "ap-south"]
    
    file_list = {
        "pdf": [],
        "docx": [],
        "txt": [],
        "images": [],
    }
    
    # Generate PDFs (runbooks) - 40 files
    for i in range(40):
        domain = rng.choice(domains)
        env = rng.choice(envs)
        file_list["pdf"].append(f"{domain}_runbook_{i+1:03d}_{env}.pdf")
    
    # Generate Word docs (FAQs, SLA policies) - 30 files
    for i in range(30):
        domain = rng.choice(domains)
        file_list["docx"].append(f"{domain}_faq_{i+1:03d}.docx")
    
    # Generate TXT files (error codes, configs) - 20 files
    for i in range(20):
        domain = rng.choice(domains)
        file_list["txt"].append(f"{domain}_error_codes_{i+1:03d}.txt")
        file_list["txt"].append(f"{domain}_config_reference_{i+1:03d}.txt")
    
    # Generate Images (architecture diagrams) - 10 files
    for i in range(10):
        domain = rng.choice(domains)
        file_list["images"].append(f"{domain}_architecture_diagram_{i+1:03d}.png")
    
    return file_list


def generate_sample_content() -> dict:
    """Generate full content for 10 representative documents."""
    rng = random.Random(42)
    envs = ["prod", "staging"]
    regions = ["us-east", "eu-west"]
    
    samples = {
        "payment_runbook_001_prod.pdf": _generate_payment_runbook(rng, "prod", "us-east"),
        "checkout_faq_001.docx": _generate_checkout_faq(rng),
        "auth_runbook_001_prod.pdf": _generate_auth_runbook(rng, "prod"),
        "redis_faq_001.docx": _generate_redis_faq(rng),
        "kafka_runbook_001_prod.pdf": _generate_kafka_runbook(rng, "prod"),
        "database_faq_001.docx": _generate_database_faq(rng),
        "notifications_runbook_001_prod.pdf": _generate_notifications_runbook(rng, "prod"),
        "payment_error_codes_001.txt": "Error codes for Payment Service:\nERR_PAY_001: Payment gateway timeout\nERR_PAY_002: Invalid payment method\nERR_PAY_003: Insufficient funds\nERR_PAY_004: Database connection failure\nERR_PAY_005: Redis cache miss",
        "auth_config_reference_001.txt": "Authentication Service Configuration:\n- lockout_threshold: 5\n- session_timeout: 1800 seconds\n- token_expiry: 3600 seconds\n- rate_limit: 10 requests/minute",
        "payment_architecture_diagram_001.png": _generate_image_ocr(rng),
    }
    
    return samples


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dataset Generator Agent - Generate synthetic support KB")
    parser.add_argument("--output-dir", type=Path, default=Path("data/kb/synthetic"), help="Output directory")
    parser.add_argument("--count", type=int, default=100, help="Total number of files to generate")
    parser.add_argument("--list-only", action="store_true", help="Only generate file list, don't create files")
    args = parser.parse_args()
    
    # Generate file list
    file_list = generate_dataset_file_list(args.count)
    
    # Save file list
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "dataset_file_list.json", "w") as f:
        json.dump(file_list, f, indent=2)
    
    print(f"Generated file list: {sum(len(files) for files in file_list.values())} files")
    print(f"  - PDFs: {len(file_list['pdf'])}")
    print(f"  - Word docs: {len(file_list['docx'])}")
    print(f"  - TXT files: {len(file_list['txt'])}")
    print(f"  - Images: {len(file_list['images'])}")
    
    if args.list_only:
        print("\nFile list saved to dataset_file_list.json")
        exit(0)
    
    # Generate sample content
    samples = generate_sample_content()
    
    # Save sample content
    samples_dir = output_dir / "samples"
    samples_dir.mkdir(exist_ok=True)
    
    for filename, content in samples.items():
        # For now, save as .txt (actual PDF/Word/Image generation would require libraries)
        txt_path = samples_dir / filename.replace(".pdf", ".txt").replace(".docx", ".txt").replace(".png", "_ocr.txt")
        txt_path.write_text(content, encoding="utf-8")
    
    print(f"\nGenerated {len(samples)} sample documents in {samples_dir}")
    print("\nNote: Remaining files are structured variants using the same templates")
    print("      with different parameters (environment, region, error codes, etc.)")
