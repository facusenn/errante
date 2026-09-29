# CLAUDE.md

## gstack

Use `/browse` skill from gstack for all web browsing needs. Never use `mcp__claude-in-chrome__*` tools.

### Available Skills

* `/office-hours` - Schedule and manage office hours
* `/plan-ceo-review` - Plan and execute CEO-level reviews
* `/plan-eng-review` - Plan and execute engineering reviews
* `/plan-design-review` - Plan and execute design reviews
* `/design-consultation` - Provide design guidance and consultations
* `/design-shotgun` - Execute rapid design iterations
* `/design-html` - Create HTML-based design assets
* `/review` - Review code and documentation
* `/ship` - Manage shipping processes
* `/land-and-deploy` - Deploy and land products
* `/canary` - Run canary testing
* `/benchmark` - Run performance benchmarks
* `/browse` - Browse web pages (gstack's primary browser skill)
* `/connect-chrome` - Connect to Chrome browser
* `/qa` - Quality assurance testing
* `/qa-only` - QA-specific testing only
* `/design-review` - Design specific reviews
* `/setup-browser-cookies` - Configure browser cookies
* `/setup-deploy` - Setup deployment configuration
* `/setup-gbrain` - Setup GBrain configuration
* `/retro` - Run retrospectives
* `/investigate` - Investigate issues and problems
* `/document-release` - Document releases
* `/document-generate` - Generate documentation
* `/codex` - Code documentation and knowledge base
* `/cso` - Chief Strategy Office functions
* `/autoplan` - Automated planning
* `/plan-devex-review` - Developer experience review planning
* `/devex-review` - Developer experience reviews
* `/careful` - Careful operation mode
* `/freeze` - Freeze operations
* `/guard` - Security/guard mode
* `/unfreeze` - Unfreeze operations
* `/gstack-upgrade` - GStack upgrades
* `/learn` - Learning and training functions

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Product ideas/brainstorming → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture → invoke /plan-eng-review
- Design system/plan review → invoke /design-consultation or /plan-design-review
- Full review pipeline → invoke /autoplan
- Bugs/errors → invoke /investigate
- QA/testing site behavior → invoke /qa or /qa-only
- Code review/diff check → invoke /review
* Visual polish → invoke /design-review
* Ship/deploy/PR → invoke /ship or /land-and-deploy
* Save progress → invoke /context-save
* Resume context → invoke /context-restore
* Author a backlog-ready spec/issue → invoke /spec