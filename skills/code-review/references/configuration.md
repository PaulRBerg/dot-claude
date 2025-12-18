# Configuration Review Reference

Expert guidance for reviewing configuration changes in production systems.

## Numeric Change Analysis

See also the 'Relative Change Analysis' section in the main skill for strategic guidance on change magnitude and risk assessment.

Assess relative changes, not absolute values. A 10% increase from 100 to 110 differs fundamentally from 10 to 11. Calculate percentage change and context impact before approval.

Apply risk thresholds by magnitude:

- **\<10%**: Low risk, proceed with standard review
- **10-50%**: Medium risk, require written justification and rollback plan
- **>50%**: High risk, demand load testing evidence and staged rollout

Calculate total risk: `risk = magnitude × blast_radius × reversibility`

Always ask: "What was the previous value?" Never review changes without baseline context. A timeout increased to 30s means nothing without knowing if it was 5s or 25s.

## Connection Pools

Size pools using the formula: `pool_size >= (threads_per_worker × worker_count)`

This ensures every thread can acquire a connection under peak load. Undersizing causes connection starvation; oversizing exhausts database connection limits.

Enforce timeout hierarchy: `client_timeout < service_timeout < database_timeout`

Each layer must fail before triggering upstream timeouts. Inverted hierarchies create cascading failures and zombie requests.

Manage idle connections to prevent:

- Database killing stale connections while pool thinks they're alive
- Firewall timeouts dropping connections without notification
- Resource waste from maintaining unnecessary connections

Common failure patterns:

- **Pool too small**: Connection starvation under normal load, request queuing, timeout spikes
- **Pool too large**: Database connection exhaustion, out-of-memory errors, connection refused failures
- **Acquisition timeout too short**: False failures during valid load spikes, unnecessary retries amplifying load

Key questions for reviewers:

- "How many concurrent users does this support?"
- "What's the database's max connection limit?"
- "What happens when all connections are in use?"

## Timeout Configurations

Coordinate upstream and downstream timeouts: `downstream_timeout < upstream_timeout`

Upstream services must outlive downstream calls. Equal timeouts create race conditions where both fail simultaneously, making debugging impossible.

Different timeout types carry different risks:

- **Connect timeout**: Affects availability perception, should be short (2-5s)
- **Read timeout**: Affects latency perception, must exceed 99th percentile response time
- **Write timeout**: Can cause data inconsistency if too short, needs careful coordination with idempotency

Integrate with circuit breakers. Timeouts trigger breakers; breakers prevent timeout storms. A timeout change often requires breaker threshold adjustment.

Watch for cascading failures. Service A times out calling Service B, but Service B completed the work. Now Service A retries, doubling Service B's load. This pattern amplifies during incidents.

## Memory and Resource Limits

Monitor GC patterns before changing heap sizes. Increasing heap doesn't solve memory leaks; it delays the inevitable crash while making GC pauses worse.

Leave headroom for OS in container constraints. A 2GB container needs ~1.5GB max heap. The OS, monitoring agents, and off-heap memory need space too.

Match buffer sizes to actual payloads. Undersized buffers cause excessive allocations; oversized buffers waste memory at scale. Measure real-world data sizes first.

Questions to answer:

- "What's the current memory usage pattern?"
- "What's the impact on garbage collection frequency and duration?"
- "What's the largest expected payload size?"

## Environment-Specific Limits

**Dev**: Relaxed for debugging convenience, verbose logging enabled, short timeouts acceptable
**Staging**: Production-like but with 20-30% safety margins, full logging for troubleshooting
**Prod**: Only battle-tested values, conservative logging, proven through staging load tests

Check proportionality: Are limits scaled to expected load per environment? Staging with 10% of prod traffic shouldn't have 100% of prod's connection pool.

Never copy values blindly across environments. Each environment serves different purposes and has different constraints.

## Monitoring Checklist

Every configuration change requires associated monitoring.

**Pool utilization**: Alert at 80%+. At 100%, you're already failing requests.

**Timeout rate**: Establish baseline first, alert on 2x increase. Absolute thresholds miss context.

**Memory pressure**: Track trends, not just thresholds. Slowly climbing memory indicates leaks; thresholds only catch late-stage failure.

**Queue depth**: Monitor producer/consumer balance. Growing queues mean consumers can't keep pace.

**Metric-per-change rule**: If you can't measure the impact, you can't verify the change worked. Every config change must have at least one metric to validate success.
