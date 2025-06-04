# Troubleshooting Guide

## Overview

This guide helps you diagnose and resolve common issues with the Freshdesk Spam Filter system.

## Quick Diagnostics

### System Health Check

Run the built-in diagnostic script:

```bash
python test_setup.py
```

This will check:
- Configuration validity
- Freshdesk API connectivity
- OLLAMA server connectivity
- Model availability

### Log Analysis

Check the application logs for errors:

```bash
# View recent logs
tail -f spam_filter.log

# Search for errors
grep -i error spam_filter.log

# Search for specific ticket issues
grep "ticket.*error" spam_filter.log
```

## Configuration Issues

### Missing Required Configuration

**Error Message:**
```
Configuration Error: Missing required configuration: FRESHDESK_DOMAIN, FRESHDESK_API_KEY
```

**Cause:** Required environment variables are not set.

**Solution:**
1. Check if `.env` file exists:
   ```bash
   ls -la .env
   ```

2. If missing, copy from example:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` file and add required values:
   ```bash
   nano .env
   ```

4. Verify configuration:
   ```bash
   python test_setup.py
   ```

### Invalid Freshdesk Domain

**Error Message:**
```
Error fetching tickets from Freshdesk: 404 Client Error
```

**Cause:** Incorrect Freshdesk domain format.

**Solution:**
1. Check domain format in `.env`:
   ```env
   # Correct formats:
   FRESHDESK_DOMAIN=company.freshdesk.com
   FRESHDESK_DOMAIN=https://company.freshdesk.com
   
   # Incorrect formats:
   FRESHDESK_DOMAIN=company  # Missing .freshdesk.com
   FRESHDESK_DOMAIN=www.company.com  # Wrong domain
   ```

2. Test domain accessibility:
   ```bash
   curl -I https://your-domain.freshdesk.com
   ```

### Invalid API Key

**Error Message:**
```
Error fetching tickets from Freshdesk: 401 Client Error: Unauthorized
```

**Cause:** Incorrect or expired API key.

**Solution:**
1. Get new API key from Freshdesk:
   - Log into Freshdesk
   - Go to Profile Settings
   - Copy API key from right sidebar

2. Update `.env` file:
   ```env
   FRESHDESK_API_KEY=your_new_api_key_here
   ```

3. Test API key:
   ```bash
   curl -u "YOUR_API_KEY:X" https://your-domain.freshdesk.com/api/v2/tickets
   ```

## OLLAMA Issues

### OLLAMA Server Not Running

**Error Message:**
```
Failed to connect to OLLAMA server at http://localhost:11434
```

**Cause:** OLLAMA server is not running.

**Solution:**
1. Check if OLLAMA is running:
   ```bash
   ps aux | grep ollama
   ```

2. Start OLLAMA server:
   ```bash
   ollama serve
   ```

3. For background operation:
   ```bash
   nohup ollama serve > ollama.log 2>&1 &
   ```

4. Verify server is responding:
   ```bash
   curl http://localhost:11434/api/tags
   ```

### Model Not Available

**Error Message:**
```
Error: model 'llama3.2' not found
```

**Cause:** Specified model is not downloaded.

**Solution:**
1. List available models:
   ```bash
   ollama list
   ```

2. Pull the required model:
   ```bash
   ollama pull llama3.2
   ```

3. For alternative models:
   ```bash
   # Smaller, faster model
   ollama pull phi3
   
   # Larger, more accurate model
   ollama pull llama3.2:8b
   ```

4. Update configuration if using different model:
   ```env
   OLLAMA_MODEL=phi3
   ```

### OLLAMA Memory Issues

**Error Message:**
```
Error: failed to load model: not enough memory
```

**Cause:** Insufficient RAM for the model.

**Solution:**
1. Check available memory:
   ```bash
   free -h
   ```

2. Use a smaller model:
   ```env
   OLLAMA_MODEL=phi3  # Requires ~2GB RAM
   ```

3. Close other applications to free memory

4. Consider upgrading system RAM

### OLLAMA Connection Timeout

**Error Message:**
```
Error: connection timeout to OLLAMA server
```

**Cause:** OLLAMA server is overloaded or unresponsive.

**Solution:**
1. Check OLLAMA server logs:
   ```bash
   tail -f ollama.log
   ```

2. Restart OLLAMA server:
   ```bash
   pkill ollama
   ollama serve
   ```

3. Reduce batch size to lower load:
   ```env
   MAX_TICKETS_PER_BATCH=10
   ```

## Freshdesk API Issues

### Rate Limiting

**Error Message:**
```
Error: 429 Too Many Requests
```

**Cause:** Exceeded Freshdesk API rate limits.

**Solution:**
1. Increase check interval:
   ```env
   CHECK_INTERVAL_MINUTES=10
   ```

2. Reduce batch size:
   ```env
   MAX_TICKETS_PER_BATCH=25
   ```

3. Check your Freshdesk plan limits

### Network Connectivity

**Error Message:**
```
Error: Connection timeout to Freshdesk API
```

**Cause:** Network connectivity issues.

**Solution:**
1. Test internet connectivity:
   ```bash
   ping google.com
   ```

2. Test Freshdesk connectivity:
   ```bash
   curl -I https://your-domain.freshdesk.com
   ```

3. Check firewall settings

4. Verify DNS resolution:
   ```bash
   nslookup your-domain.freshdesk.com
   ```

### Permission Issues

**Error Message:**
```
Error: 403 Forbidden - Insufficient privileges
```

**Cause:** API key lacks required permissions.

**Solution:**
1. Check API key permissions in Freshdesk
2. Ensure account has ticket management permissions
3. Contact Freshdesk administrator for permission updates

## Application Issues

### No Tickets Found

**Error Message:**
```
No new tickets found to process
```

**Cause:** No new tickets or filtering too restrictive.

**Solution:**
1. Check if there are actually new tickets in Freshdesk

2. Verify ticket status filtering:
   ```env
   PROCESS_NEW_TICKETS_ONLY=true  # Only processes status=2 (Open)
   ```

3. Temporarily disable new-only filtering:
   ```env
   PROCESS_NEW_TICKETS_ONLY=false
   ```

4. Check ticket creation time vs. last run time

### High False Positive Rate

**Symptoms:** Legitimate tickets being marked as spam.

**Solution:**
1. Increase spam threshold:
   ```env
   SPAM_THRESHOLD=0.8  # More conservative
   ```

2. Try a different model:
   ```env
   OLLAMA_MODEL=llama3.2:8b  # More accurate
   ```

3. Review AI reasoning in logs:
   ```bash
   grep -A 5 -B 5 "confidence.*0\.[89]" spam_filter.log
   ```

4. Manually review tagged tickets in Freshdesk

### High False Negative Rate

**Symptoms:** Spam tickets not being detected.

**Solution:**
1. Decrease spam threshold:
   ```env
   SPAM_THRESHOLD=0.6  # More sensitive
   ```

2. Check if spam tickets have unusual characteristics

3. Review AI reasoning for missed spam:
   ```bash
   grep -A 5 -B 5 "confidence.*0\.[23]" spam_filter.log
   ```

### Processing Errors

**Error Message:**
```
Error processing ticket 12345: KeyError: 'description'
```

**Cause:** Unexpected ticket data format.

**Solution:**
1. Check ticket data structure in logs

2. Enable debug logging:
   ```env
   LOG_LEVEL=DEBUG
   ```

3. Review specific ticket in Freshdesk

4. Check for missing required fields

## Performance Issues

### Slow Processing

**Symptoms:** Taking too long to process tickets.

**Causes and Solutions:**

1. **Large AI Model:**
   ```env
   OLLAMA_MODEL=phi3  # Faster, smaller model
   ```

2. **Large Batch Size:**
   ```env
   MAX_TICKETS_PER_BATCH=25  # Reduce batch size
   ```

3. **Network Latency:**
   - Use local OLLAMA server
   - Optimize network connection

4. **System Resources:**
   - Check CPU and memory usage
   - Close unnecessary applications

### High Memory Usage

**Symptoms:** System running out of memory.

**Solution:**
1. Use smaller AI model:
   ```env
   OLLAMA_MODEL=phi3
   ```

2. Reduce batch size:
   ```env
   MAX_TICKETS_PER_BATCH=10
   ```

3. Monitor memory usage:
   ```bash
   top -p $(pgrep python)
   ```

## Logging and Debugging

### Enable Debug Logging

```env
LOG_LEVEL=DEBUG
```

### Useful Log Searches

```bash
# Find configuration issues
grep -i "config" spam_filter.log

# Find API errors
grep -i "api.*error" spam_filter.log

# Find spam detection results
grep "confidence" spam_filter.log

# Find processing statistics
grep "Total Processed" spam_filter.log
```

### Log File Locations

- **Application Log:** `spam_filter.log`
- **OLLAMA Log:** `ollama.log` (if redirected)
- **System Log:** `/var/log/syslog` (Linux)

## Error Codes Reference

### HTTP Status Codes

- **401 Unauthorized:** Invalid API key
- **403 Forbidden:** Insufficient permissions
- **404 Not Found:** Invalid domain or endpoint
- **429 Too Many Requests:** Rate limit exceeded
- **500 Internal Server Error:** Freshdesk server issue

### Application Exit Codes

- **0:** Success
- **1:** Configuration error
- **2:** Connection error
- **3:** Processing error

## Getting Help

### Before Seeking Help

1. Check this troubleshooting guide
2. Review application logs
3. Run diagnostic script: `python test_setup.py`
4. Try basic solutions (restart, reconfigure)

### Information to Provide

When reporting issues, include:

1. **Error Message:** Exact error text
2. **Configuration:** Relevant `.env` settings (mask sensitive data)
3. **Logs:** Recent log entries around the error
4. **Environment:** OS, Python version, OLLAMA version
5. **Steps to Reproduce:** What you were doing when error occurred

### Log Sanitization

Before sharing logs, remove sensitive information:

```bash
# Remove API keys and domains
sed 's/FRESHDESK_API_KEY=.*/FRESHDESK_API_KEY=***REDACTED***/g' spam_filter.log | \
sed 's/your-domain\.freshdesk\.com/***DOMAIN***/g'
```

## Recovery Procedures

### Complete System Reset

```bash
# Stop application
pkill -f "python main.py"

# Reset configuration
cp .env.example .env
nano .env  # Reconfigure

# Clear logs
> spam_filter.log

# Restart OLLAMA
pkill ollama
ollama serve &

# Test configuration
python test_setup.py

# Restart application
python main.py
```

### Partial Recovery

```bash
# Restart just the application
pkill -f "python main.py"
python main.py

# Or restart just OLLAMA
pkill ollama
ollama serve &
```
