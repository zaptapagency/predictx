# 🔍 PredictX Troubleshooting & Monitoring Guide

Complete guide for monitoring, debugging, and resolving issues in production.

---

## Quick Health Check

```bash
# 1. Backend health
curl https://your-api.com/health

# 2. Database connectivity
railway run psql -c "SELECT 1"

# 3. View logs
railway logs -f

# 4. Check variables
railway variable list

# 5. Frontend status
curl https://your-frontend.com
```

---

## Monitoring Production

### Railway Dashboard

Access: https://railway.app

**Monitor**:
- Deployments (active/failed)
- Logs (real-time)
- CPU/Memory usage
- Database connections
- Network latency
- Crash reports

**Commands**:
```bash
# Follow logs
railway logs -f

# Filter errors
railway logs | grep ERROR

# Filter API calls
railway logs | grep "POST\|GET\|PUT\|DELETE"

# Last 100 lines
railway logs --head 100
```

### Vercel Dashboard

Access: https://vercel.com/dashboard

**Monitor**:
- Deployment status
- Build times
- Web vitals
- Error logs
- Performance metrics

### Stripe Dashboard

Access: https://dashboard.stripe.com

**Monitor**:
- Payment success rate
- Failed payments
- Webhook deliveries
- Revenue metrics
- Customer list

**Webhook logs**: Dashboard → Webhooks → Select endpoint → Logs

### Email Status

**Gmail**:
- Account: https://accounts.google.com/security
- App passwords: Check if still valid
- SMTP settings: Verify in backend logs

**Monitor**:
- Sent emails: Gmail sent folder
- Failed sends: Check backend logs
- Bounce rate: Monitor Stripe invoices

---

## Debugging Common Issues

### Issue: Backend Not Responding

```bash
# 1. Check if service is running
railway status

# 2. View logs
railway logs

# 3. Check CPU/Memory
railway logs | grep -E "CPU|Memory"

# 4. Restart service
railway up

# 5. Check database
railway run psql -c "SELECT 1"

# 6. Check environment
railway variable list
```

**Resolution**:
- Increase memory: Railway dashboard → Settings → Plan
- Check for infinite loops in code
- Review recent deployments for errors

### Issue: Database Connection Timeout

```bash
# 1. Verify URL
railway variable get DATABASE_URL

# 2. Test connection
railway run psql -c "SELECT 1"

# 3. Check connection count
railway run psql -c "SELECT count(*) FROM pg_stat_activity"

# 4. Kill idle connections
railway run psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = ''idle''"

# 5. Check table sizes
railway run psql -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||''.''||tablename)) FROM pg_tables ORDER BY pg_total_relation_size DESC LIMIT 10"
```

**Resolution**:
- Upgrade database plan if hitting connection limits
- Review slow queries
- Add indexes to frequently queried columns

### Issue: Email Not Sending

```bash
# 1. Check SMTP config
railway variable list | grep SMTP

# 2. View email logs
railway logs | grep -i "email\|mail\|smtp"

# 3. Check app password valid
# Gmail: https://accounts.google.com/account/security

# 4. Test manually
curl -X POST https://your-api.com/api/auth/password-reset \
  -H "Content-Type: application/json" \
  -d ''{"email": "your-test@example.com"}''
```

**Resolution**:
- Regenerate Gmail app password
- Check SMTP_USER is full email
- Verify SMTP_PORT is correct (587 for Gmail)
- Review Gmail security settings
- Switch to SendGrid/Mailtrap if needed

### Issue: Stripe Webhook Not Working

```bash
# 1. Check webhook secret
railway variable get STRIPE_WEBHOOK_SECRET

# 2. View webhook logs
# Go to: https://dashboard.stripe.com/webhooks
# Click endpoint → Logs tab
# Check delivery attempts and responses

# 3. Test webhook manually
curl -X POST https://your-api.com/api/webhooks/stripe \
  -H "Content-Type: application/json" \
  -d ''{"type": "ping"}''

# 4. Check backend logs
railway logs | grep webhook
```

**Resolution**:
- Verify webhook secret matches Stripe dashboard
- Ensure backend URL is public (not localhost)
- Check that POST endpoint is accepting requests
- Add webhook event listeners to backend
- Monitor Stripe webhook logs for delivery status

### Issue: Login Not Working

```bash
# 1. Check JWT secret
railway variable get JWT_SECRET_KEY

# 2. Test login API
curl -X POST https://your-api.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d ''{
    "email": "test@example.com",
    "password": "password"
  }''

# 3. Check database
railway run psql -c "SELECT email, is_verified FROM users LIMIT 5"

# 4. View logs
railway logs | grep -i "login\|auth"
```

**Resolution**:
- Check user exists in database: `SELECT * FROM users WHERE email = ''email@example.com''`
- Verify password hash stored: `SELECT id, password_hash FROM users LIMIT 1`
- Check if user email is verified: `is_verified` column
- Review JWT token generation in logs

### Issue: Slow API Response

```bash
# 1. Check CPU/Memory
railway logs | grep -E "CPU|Memory"

# 2. View slow queries
railway run psql -c "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10"

# 3. Check active connections
railway run psql -c "SELECT * FROM pg_stat_activity WHERE state != ''idle''"

# 4. View backend logs
railway logs | grep -E "TIMING|latency|slow"
```

**Resolution**:
- Add database indexes to slow queries
- Optimize N+1 queries in code
- Implement caching (Redis)
- Upgrade database to higher tier
- Review and optimize FastAPI endpoints

### Issue: High Memory Usage

```bash
# 1. Check memory allocation
railway logs | grep Memory

# 2. Check process memory
railway shell
# Once connected:
ps aux | grep python
free -h
# exit

# 3. Check for memory leaks
railway logs | tail -1000 | grep -i "memory\|leak"
```

**Resolution**:
- Increase Railway plan memory
- Review code for memory leaks
- Implement connection pooling
- Cache query results
- Limit response payload sizes

### Issue: Database Disk Space

```bash
# 1. Check disk usage
railway run psql -c "SELECT pg_size_pretty(pg_database_size(current_database()))"

# 2. List largest tables
railway run psql -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||''.''||tablename)) FROM pg_tables ORDER BY pg_total_relation_size DESC"

# 3. Cleanup old data
# Delete logs older than 30 days (example):
railway run psql -c "DELETE FROM usage_logs WHERE created_at < now() - interval ''30 days''"

# 4. Vacuum database
railway run psql -c "VACUUM ANALYZE"
```

**Resolution**:
- Archive old data
- Implement data retention policies
- Upgrade to larger database
- Add table indexes
- Remove duplicate records

---

## Performance Optimization

### Database Optimization

```bash
# 1. Add indexes to frequently queried columns
railway run psql -c "CREATE INDEX idx_users_email ON users(email)"
railway run psql -c "CREATE INDEX idx_predictions_user ON predictions(user_id)"

# 2. Vacuum and analyze
railway run psql -c "VACUUM ANALYZE"

# 3. Check index usage
railway run psql -c "SELECT schemaname, tablename, indexname, idx_scan FROM pg_stat_user_indexes ORDER BY idx_scan DESC"
```

### API Optimization

```python
# Use Redis caching
@app.get("/api/users/me")
async def get_user(current_user: User = Depends(get_current_user)):
    # Cache key: user:{user_id}
    cache_key = f"user:{current_user.id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Fetch from DB
    user = await db.get(User, current_user.id)
    
    # Cache for 1 hour
    await redis.setex(cache_key, 3600, json.dumps(user))
    return user
```

### Query Optimization

```bash
# Identify slow queries
railway run psql -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10"

# Explain query plan
railway run psql -c "EXPLAIN ANALYZE SELECT * FROM users WHERE email = ''test@example.com''"
```

---

## Backup & Recovery

### Database Backup

```bash
# Railway auto-backs up PostgreSQL
# Access via Railway dashboard

# Manual backup
railway run pg_dump -Fc > backup.dump

# Restore
railway run pg_restore -d dbname backup.dump
```

### Data Recovery

```bash
# List recent backups
railway logs | grep backup

# Restore from backup
# Contact Railway support or use restore from backup in dashboard
```

---

## Monitoring Setup (Optional)

### Sentry Error Tracking

```bash
# Install Sentry
pip install sentry-sdk

# Add to FastAPI
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://your-sentry-dsn@sentry.io/project",
    integrations=[FastApiIntegration()]
)
```

### UptimeRobot Monitoring

1. Go to https://uptimerobot.com
2. Add monitor: https://your-api.com/health
3. Alert on downtime
4. Check every 5 minutes

### Performance Monitoring

```bash
# View API response times
railway logs | grep "response_time"

# Calculate median latency
railway logs | grep "response_time" | awk ''{print $NF}'' | sort -n | head -50%
```

---

## Alerting Setup

### Email Alerts

```bash
# When backend goes down
railway logs | grep "ERROR" | mail -s "PredictX Alert" admin@example.com

# Set as cron job (every 5 minutes)
*/5 * * * * railway logs --head 100 | grep ERROR | mail -s "PredictX Errors" admin@example.com
```

### Webhook Alerts

```bash
# Send alert to Slack
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK \
  -H "Content-Type: application/json" \
  -d ''{"text": "PredictX Backend Error"}''
```

---

## Maintenance Tasks

### Weekly
- [ ] Review backend logs for errors
- [ ] Check Stripe webhook deliveries
- [ ] Monitor database disk usage
- [ ] Verify email sending works

### Monthly
- [ ] Backup data manually
- [ ] Review slow queries
- [ ] Update dependencies
- [ ] Check security patches
- [ ] Review cost usage

### Quarterly
- [ ] Rotate API keys
- [ ] Review access logs
- [ ] Optimize database
- [ ] Load testing
- [ ] Security audit

---

## Contact & Support

### Railway Support
- Status: https://status.railway.app
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway
- Email: support@railway.app

### Stripe Support
- Dashboard: https://dashboard.stripe.com
- Docs: https://stripe.com/docs
- Support: https://support.stripe.com

### Vercel Support
- Dashboard: https://vercel.com
- Docs: https://vercel.com/docs
- Support: https://support.vercel.com
