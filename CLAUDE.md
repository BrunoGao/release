# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a comprehensive CI/CD infrastructure setup for Mac Studio M2 environment, featuring Jenkins, Gitea, and Docker Registry with full automation support.

## Quick Start Commands

```bash
# Complete automated deployment - fully configured Jenkins
./jenkins-auto-deploy.sh

# Daily management
./jenkins-manager.sh start     # Start services
./jenkins-manager.sh stop      # Stop services  
./jenkins-manager.sh status    # Check status
./jenkins-manager.sh logs      # View Jenkins logs
./jenkins-manager.sh backup    # Backup configuration
./jenkins-manager.sh health    # Health check

# Simple quick start (manual setup required)
./quick-start-jenkins.sh
```

## Service Access Points

- **Jenkins**: http://localhost:8081 (admin/admin123 for auto-deployed)
- **Docker Registry**: http://localhost:5001
- **Registry UI**: http://localhost:5002  
- **Gitea**: http://192.168.1.6:3000

## Architecture

### Core Components
- **Jenkins LTS**: CI/CD server with Configuration as Code (CasC)
- **Gitea**: Git repository server with Actions support
- **Docker Registry**: Local container registry for multi-platform images
- **Multi-platform Build**: Supports linux/amd64 and linux/arm64

### Key Directories
```
infra/
├── jenkins-auto-deploy.sh              # ⭐ Main automated deployment
├── jenkins-manager.sh                  # Daily management script
├── docker/compose/
│   ├── jenkins-simple.yml             # Primary Jenkins Compose file
│   ├── jenkins-complete-auto.yml       # Full auto-configuration
│   └── jenkins/
│       ├── casc/jenkins.yaml          # ⭐ Configuration as Code
│       ├── plugins.txt                # Jenkins plugins list
│       ├── init-scripts/              # Initialization scripts
│       ├── shared-library/            # Pipeline shared libraries
│       └── templates/                 # Dockerfile & Pipeline templates
├── deployment/scripts/                # Management & integration scripts
└── docs/                              # Documentation and guides
```

## Docker Configuration Files

### Main Compose Files
- `jenkins-simple.yml` - Basic Jenkins setup
- `jenkins-complete-auto.yml` - Full automation with CasC
- `gitea-compose.yml` - Gitea service
- `registry-compose.yml` - Docker registry

### Jenkins Automation
The Jenkins instance uses Configuration as Code located at `docker/compose/jenkins/casc/jenkins.yaml` which includes:
- Auto-configured tools (Git, Maven, Gradle, NodeJS, Docker, Python)
- Pre-configured credentials (Gitea, Registry, SSH)
- Cloud configurations (Docker, Kubernetes)
- Security settings and user management
- Pre-created jobs (multi-platform builds, system monitoring)

## Development Workflow

### For Infrastructure Changes
1. Modify configuration files in `docker/compose/jenkins/casc/`
2. Test with: `./jenkins-manager.sh restart`
3. Use: `./jenkins-manager.sh health` to verify

### For Adding New Services
1. Create/modify compose files in `docker/compose/`
2. Update management scripts in `deployment/scripts/`
3. Test deployment with appropriate script

### Pipeline Development
- Templates available in `docker/compose/jenkins/templates/`
- Shared libraries in `docker/compose/jenkins/shared-library/`
- Multi-platform Docker builds supported by default

## Important Configuration Files

- `docker/compose/jenkins/casc/jenkins.yaml` - Jenkins Configuration as Code
- `docker/compose/jenkins/plugins.txt` - Jenkins plugins
- `jenkins-manager.sh` - Primary management interface
- `deployment/scripts/` - Various automation scripts

## Multi-Platform Build Support

All Docker builds support both linux/amd64 and linux/arm64 platforms. The Jenkins configuration includes buildx setup and multi-platform pipeline templates.

## Backup and Recovery

```bash
./jenkins-manager.sh backup    # Create backup
./jenkins-manager.sh restore   # Restore from backup
```

Backups are stored in `backup/jenkins/` with timestamps.

## Troubleshooting

1. Check service health: `./jenkins-manager.sh health`
2. View logs: `./jenkins-manager.sh logs`
3. Restart services: `./jenkins-manager.sh restart`
4. Full reset: `./jenkins-manager.sh cleanup` (⚠️ destructive)

Detailed troubleshooting guide available at `docs/troubleshooting.md`.