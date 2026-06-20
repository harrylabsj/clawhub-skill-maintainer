## Description: <br>
Maintain a large ClawHub skill portfolio with a quality-first and AI-assisted upgrade lens. Use when the user wants to audit published skills, find high-quality skills worth maintaining, analyze downloads/installs/stars/comments, detect stale or partial data, generate safe upgrade/maintenance queues, prepare AI maintainer prompts, handle bulk-publishing account risk, or build/update a ClawHub skill dashboard. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[harrylabsj](https://clawhub.ai/user/harrylabsj) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers, maintainers, and ClawHub publishers use this skill to audit published skill portfolios, identify skills worth long-term maintenance, review usage and quality signals, plan AI-assisted upgrades, and generate dashboard, prompt, and approval artifacts. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill can recommend public visibility, publish, rescan, or merge actions that affect a ClawHub portfolio. <br>
Mitigation: Review generated approval boards carefully and execute only the exact batch explicitly approved by the user; cleanup batches are suppressed when data quality is partial, and merge batches remain higher risk because reversibility is not established. <br>
Risk: The skill gathers ClawHub portfolio data and writes local reports and snapshots. <br>
Mitigation: Install and run it only for portfolio maintenance workflows, review local generated artifacts before acting on them, and clearly state when network or authentication limits the analysis. <br>


## Reference(s): <br>
- [ClawHub Skill Page](https://clawhub.ai/harrylabsj/skill-maintainer) <br>
- [Publisher Profile](https://clawhub.ai/user/harrylabsj) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, code, shell commands, configuration, guidance] <br>
**Output Format:** [Markdown guidance with inline shell commands, local JSON/CSV/HTML report files, AI maintainer prompts, and approval board artifacts] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Generated action commands are approval previews and require explicit user approval before execution.] <br>

## Skill Version(s): <br>
1.3.0 (source: AI-assisted auto-upgrade planning and safe edit gates) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
