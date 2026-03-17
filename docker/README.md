# Odoo Setup Guide for AI Employee Gold Tier

## Quick Start

### 1. Prerequisites

- Docker Desktop installed and running
- At least 4GB RAM available for Odoo
- 10GB free disk space

### 2. Initial Setup

```bash
# Navigate to docker directory
cd docker

# Copy environment file
cp .env.example .env

# Edit .env with your secure passwords
# IMPORTANT: Change default passwords before production use!
```

### 3. Start Odoo

```bash
# Start Odoo and PostgreSQL
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f odoo
```

### 4. Access Odoo

- **Odoo Web Interface:** http://localhost:8069
- **PgAdmin (Database Admin):** http://localhost:8080

### 5. First-Time Configuration

1. Open http://localhost:8069 in your browser
2. Create master password (use ODOO_ADMIN_PASSWORD from .env)
3. Create new database:
   - Database name: odoo_db
   - Email: your-email@example.com
   - Password: your-admin-password
4. Install required apps:
   - **Accounting** (Invoicing module for community edition)
   - **CRM** (Customer relationship management)
   - **Projects** (Project management)
   - **Contacts** (Contact management)

### 6. Configure Accounting

1. Go to **Accounting** app
2. Complete accounting setup wizard
3. Configure:
   - Company information
   - Chart of accounts
   - Taxes
   - Bank accounts
   - Fiscal year

### 7. API Access Setup

For MCP server integration:

1. Go to **Settings** → **Users & Companies** → **Users**
2. Create API user (e.g., "ai_employee")
3. Set strong password
4. Grant permissions:
   - Accounting / User
   - Invoicing / User
   - Technical / API Access
5. Note credentials for MCP server configuration

### 8. Configure Odoo MCP Server

Create `.env` file in project root:

```bash
# Odoo API Configuration
ODOO_URL=http://localhost:8069
ODOO_DB=odoo_db
ODOO_USERNAME=ai_employee
ODOO_PASSWORD=your-api-user-password
ODOO_API_KEY=optional-api-key-if-configured
```

### 9. Test Connection

```bash
# Test Odoo MCP connection
python scripts/odoo_mcp_test.py
```

## Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f odoo
docker-compose logs -f postgres

# Backup database
docker-compose exec postgres pg_dump -U odoo odoo_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U odoo odoo_db < backup.sql

# Update Odoo
docker-compose pull
docker-compose up -d

# Remove all data (WARNING: destructive!)
docker-compose down -v
```

## Troubleshooting

### Odoo Won't Start

```bash
# Check logs
docker-compose logs odoo

# Restart database first
docker-compose restart postgres
docker-compose restart odoo
```

### Database Connection Error

```bash
# Verify database is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres
```

### Port Already in Use

Edit `docker-compose.yml` and change port mapping:
```yaml
ports:
  - "8070:8069"  # Use 8070 instead of 8069
```

### Out of Memory

Increase Docker memory limit in Docker Desktop settings or reduce workers in odoo.conf.

## Production Deployment

For cloud VM deployment:

1. Use a public IP or domain
2. Configure HTTPS with reverse proxy (nginx/traefik)
3. Set up automated backups
4. Configure proper SMTP for emails
5. Enable Odoo workers for performance
6. Set up monitoring and alerts

### Example Nginx Configuration

```nginx
server {
    listen 80;
    server_name odoo.yourdomain.com;

    location / {
        proxy_pass http://localhost:8069;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Security Best Practices

1. **Change all default passwords**
2. **Use environment variables** for sensitive data
3. **Enable HTTPS** in production
4. **Regular backups** (daily recommended)
5. **Keep Odoo updated** (security patches)
6. **Limit API user permissions** to minimum required
7. **Monitor access logs** for suspicious activity
8. **Use firewall rules** to restrict access

## Integration with AI Employee

Once Odoo is running:

1. Ensure Odoo MCP server is configured
2. Test invoice creation via MCP
3. Configure accounting workflows
4. Set up automated financial reporting
5. Enable CEO Briefing integration

## Next Steps

- Configure Odoo modules for your business needs
- Set up automated invoice generation
- Configure payment tracking
- Create custom reports
- Integrate with other AI Employee components

## Support Resources

- [Odoo Documentation](https://www.odoo.com/documentation/19.0/)
- [Odoo Community Forum](https://www.odoo.com/forum/help-1)
- [Odoo GitHub Issues](https://github.com/odoo/odoo/issues)
