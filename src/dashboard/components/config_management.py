"""
Configuration Management Components for Trading Dashboard

This module provides Streamlit components for dynamic configuration management,
including real-time editing, validation, backup/restore, and version control.
"""

import streamlit as st
import json
import yaml
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.orchestrator.config_manager import get_dynamic_config_manager, ConfigChangeType
from src.orchestrator import get_agent_manager


def render_configuration_management():
    """Main configuration management interface."""
    st.markdown("### ⚙️ Configuration Management")

    config_manager = get_dynamic_config_manager()

    # Configuration tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔧 Live Config", "📋 Agent Configs", "📊 History", "💾 Backup/Restore", "📄 Templates"
    ])

    with tab1:
        render_live_configuration()

    with tab2:
        render_agent_configurations()

    with tab3:
        render_configuration_history()

    with tab4:
        render_backup_restore()

    with tab5:
        render_configuration_templates()


def render_live_configuration():
    """Render live configuration editing interface."""
    st.markdown("#### 🔧 Live Configuration Editor")

    config_manager = get_dynamic_config_manager()
    current_config = config_manager.get_current_configuration()

    if not current_config:
        st.warning("No configuration loaded. Please check your configuration files.")
        return

    # Configuration reload button
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown("**Real-time Configuration Management**")

    with col2:
        if st.button("🔄 Reload Config", use_container_width=True):
            with st.spinner("Reloading configuration..."):
                import asyncio
                success = asyncio.run(config_manager.reload_configuration())
                if success:
                    st.success("✅ Configuration reloaded successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to reload configuration")

    with col3:
        if st.button("💾 Save Changes", use_container_width=True):
            with st.spinner("Saving configuration..."):
                try:
                    import asyncio
                    asyncio.run(config_manager.save_configuration())
                    st.success("✅ Configuration saved successfully!")
                except Exception as e:
                    st.error(f"❌ Failed to save configuration: {e}")

    st.markdown("---")

    # Dashboard Configuration
    st.markdown("##### 🏠 Dashboard Configuration")

    dashboard_config = current_config.get("dashboard", {})

    col1, col2 = st.columns(2)

    with col1:
        title = st.text_input("Dashboard Title", value=dashboard_config.get("title", "Trading Dashboard"))
        port = st.number_input("Port", value=dashboard_config.get("port", 8501), min_value=1024, max_value=65535)
        debug = st.checkbox("Debug Mode", value=dashboard_config.get("debug", False))

    with col2:
        subtitle = st.text_input("Subtitle", value=dashboard_config.get("subtitle", "Autonomous Trading System"))
        host = st.text_input("Host", value=dashboard_config.get("host", "localhost"))
        refresh_interval = st.number_input("Refresh Interval (s)", value=dashboard_config.get("refresh_interval", 30), min_value=1)

    # Apply dashboard changes button
    if st.button("🔄 Apply Dashboard Changes"):
        dashboard_updates = {
            "title": title,
            "subtitle": subtitle,
            "port": port,
            "host": host,
            "debug": debug,
            "refresh_interval": refresh_interval
        }

        with st.spinner("Applying dashboard configuration changes..."):
            # Update in-memory config
            current_config["dashboard"].update(dashboard_updates)
            st.success("✅ Dashboard configuration updated! Restart required for some changes.")

    st.markdown("---")

    # Logging Configuration
    st.markdown("##### 📝 Logging Configuration")

    logging_config = current_config.get("logging", {})

    col1, col2 = st.columns(2)

    with col1:
        log_level = st.selectbox(
            "Log Level",
            ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            index=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].index(
                logging_config.get("level", "INFO")
            )
        )
        console_output = st.checkbox("Console Output", value=logging_config.get("console_output", True))

    with col2:
        max_file_size = st.text_input("Max File Size", value=logging_config.get("max_file_size", "10MB"))
        backup_count = st.number_input("Backup Count", value=logging_config.get("backup_count", 5), min_value=1, max_value=50)

    # Apply logging changes button
    if st.button("🔄 Apply Logging Changes"):
        logging_updates = {
            "level": log_level,
            "console_output": console_output,
            "max_file_size": max_file_size,
            "backup_count": backup_count
        }

        with st.spinner("Applying logging configuration changes..."):
            current_config["logging"].update(logging_updates)
            st.success("✅ Logging configuration updated!")

    # Raw configuration editor (advanced)
    with st.expander("🔧 Advanced: Raw Configuration Editor"):
        st.warning("⚠️ Advanced users only. Invalid configurations may cause system instability.")

        config_json = st.text_area(
            "Raw Configuration (JSON)",
            value=json.dumps(current_config, indent=2),
            height=400,
            help="Edit the raw configuration in JSON format. Use with caution."
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔍 Validate JSON"):
                try:
                    parsed_config = json.loads(config_json)
                    import asyncio
                    validation_result = asyncio.run(config_manager.validate_configuration(parsed_config))

                    if validation_result["valid"]:
                        st.success("✅ Configuration is valid!")
                    else:
                        st.error("❌ Configuration validation failed:")
                        for error in validation_result["errors"]:
                            st.error(f"• {error}")

                        for warning in validation_result.get("warnings", []):
                            st.warning(f"• {warning}")

                except json.JSONDecodeError as e:
                    st.error(f"❌ Invalid JSON: {e}")

        with col2:
            if st.button("💾 Apply Raw Changes"):
                try:
                    parsed_config = json.loads(config_json)
                    import asyncio

                    # Validate before applying
                    validation_result = asyncio.run(config_manager.validate_configuration(parsed_config))

                    if validation_result["valid"]:
                        # Apply configuration
                        config_manager.current_config = parsed_config
                        asyncio.run(config_manager.save_configuration())
                        st.success("✅ Raw configuration applied successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Cannot apply invalid configuration")

                except (json.JSONDecodeError, Exception) as e:
                    st.error(f"❌ Failed to apply configuration: {e}")


def render_agent_configurations():
    """Render agent-specific configuration management."""
    st.markdown("#### 📋 Agent Configuration Management")

    config_manager = get_dynamic_config_manager()
    current_config = config_manager.get_current_configuration()
    agents_config = current_config.get("agents", {})

    if not agents_config:
        st.info("No agents configured.")
        return

    # Agent selection
    selected_agent = st.selectbox(
        "Select Agent to Configure",
        list(agents_config.keys()),
        help="Choose an agent to view and modify its configuration"
    )

    if selected_agent:
        agent_config = agents_config[selected_agent]

        st.markdown(f"##### ⚙️ Configuration for {agent_config.get('name', selected_agent)}")

        # Agent configuration form
        col1, col2 = st.columns(2)

        with col1:
            agent_name = st.text_input("Agent Name", value=agent_config.get("name", selected_agent))
            agent_url = st.text_input("Agent URL", value=agent_config.get("url", ""))
            agent_enabled = st.checkbox("Enabled", value=agent_config.get("enabled", True))

        with col2:
            timeout = st.number_input("Timeout (seconds)", value=agent_config.get("timeout", 30), min_value=1, max_value=300)
            health_check_interval = st.number_input("Health Check Interval", value=agent_config.get("health_check_interval", 60), min_value=10)
            max_retries = st.number_input("Max Retries", value=agent_config.get("max_retries", 3), min_value=0, max_value=10)

        # Advanced agent settings
        with st.expander("🔧 Advanced Agent Settings"):
            col1, col2 = st.columns(2)

            with col1:
                agent_dependencies = st.text_area(
                    "Dependencies (one per line)",
                    value="\n".join(agent_config.get("dependencies", [])),
                    help="List agent dependencies, one per line"
                )

            with col2:
                agent_priority = st.number_input("Priority", value=agent_config.get("priority", 50), min_value=1, max_value=100)
                restart_policy = st.selectbox(
                    "Restart Policy",
                    ["immediate", "delayed", "exponential_backoff", "manual"],
                    index=["immediate", "delayed", "exponential_backoff", "manual"].index(
                        agent_config.get("restart_policy", "immediate")
                    )
                )

        # Update agent configuration
        if st.button(f"💾 Update {selected_agent} Configuration", use_container_width=True):
            agent_updates = {
                "name": agent_name,
                "url": agent_url,
                "enabled": agent_enabled,
                "timeout": timeout,
                "health_check_interval": health_check_interval,
                "max_retries": max_retries,
                "dependencies": [dep.strip() for dep in agent_dependencies.split('\n') if dep.strip()],
                "priority": agent_priority,
                "restart_policy": restart_policy
            }

            with st.spinner(f"Updating {selected_agent} configuration..."):
                import asyncio
                success = asyncio.run(config_manager.update_agent_configuration(selected_agent, agent_updates))

                if success:
                    st.success(f"✅ {selected_agent} configuration updated successfully!")

                    # Restart agent if it's running (with confirmation)
                    agent_manager = get_agent_manager()
                    if selected_agent in agent_manager.agents:
                        agent_status = agent_manager.get_agent_status(selected_agent)
                        if str(agent_status) == "AgentStatus.RUNNING":
                            if st.button("🔄 Restart Agent to Apply Changes", type="secondary"):
                                with st.spinner(f"Restarting {selected_agent}..."):
                                    restart_result = asyncio.run(agent_manager.restart_agent(selected_agent))
                                    if restart_result:
                                        st.success(f"✅ {selected_agent} restarted successfully!")
                                    else:
                                        st.error(f"❌ Failed to restart {selected_agent}")

                    st.rerun()
                else:
                    st.error(f"❌ Failed to update {selected_agent} configuration")

        # Add new agent
        st.markdown("---")
        st.markdown("##### ➕ Add New Agent")

        with st.expander("Add New Agent Configuration"):
            new_agent_name = st.text_input("New Agent Name", placeholder="e.g., pattern_recognition")
            new_agent_url = st.text_input("New Agent URL", placeholder="http://localhost:8001/health")

            if st.button("➕ Add Agent"):
                if new_agent_name and new_agent_url:
                    new_agent_config = {
                        "name": new_agent_name.replace("_", " ").title(),
                        "url": new_agent_url,
                        "enabled": True,
                        "timeout": 30,
                        "health_check_interval": 60,
                        "max_retries": 3,
                        "dependencies": [],
                        "priority": 50
                    }

                    with st.spinner(f"Adding {new_agent_name}..."):
                        import asyncio
                        success = asyncio.run(config_manager.update_agent_configuration(new_agent_name, new_agent_config))

                        if success:
                            st.success(f"✅ Agent {new_agent_name} added successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to add agent {new_agent_name}")
                else:
                    st.error("Please provide both agent name and URL")


def render_configuration_history():
    """Render configuration change history."""
    st.markdown("#### 📊 Configuration Change History")

    config_manager = get_dynamic_config_manager()

    # History controls
    col1, col2, col3 = st.columns(3)

    with col1:
        history_limit = st.number_input("Show Last N Changes", value=20, min_value=5, max_value=100)

    with col2:
        if st.button("🔄 Refresh History"):
            st.rerun()

    with col3:
        if st.button("📥 Export History"):
            history = config_manager.get_configuration_history(limit=100)
            history_json = json.dumps(history, indent=2, default=str)
            st.download_button(
                label="💾 Download History JSON",
                data=history_json,
                file_name=f"config_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

    # Configuration history display
    history = config_manager.get_configuration_history(limit=history_limit)

    if not history:
        st.info("No configuration history available.")
        return

    # History table
    st.markdown("##### 📜 Recent Configuration Changes")

    history_data = []
    for change in reversed(history):  # Show most recent first
        timestamp = datetime.fromtimestamp(change["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        change_type = change["change_type"]
        section = change.get("config_section", "N/A")
        message = change.get("message", "No message")

        # Color code change types
        type_colors = {
            "CREATED": "🟢",
            "MODIFIED": "🟡",
            "DELETED": "🔴",
            "RELOADED": "🔄",
            "VALIDATED": "✅",
            "RESTORED": "📥"
        }

        icon = type_colors.get(change_type, "📝")

        history_data.append({
            "Time": timestamp,
            "Type": f"{icon} {change_type}",
            "Section": section,
            "Message": message[:100] + ("..." if len(message) > 100 else "")
        })

    if history_data:
        st.dataframe(history_data, use_container_width=True)

    # Configuration versions
    st.markdown("---")
    st.markdown("##### 📋 Configuration Versions")

    versions = config_manager.get_configuration_versions()

    if versions:
        version_data = []
        for version in reversed(versions[-10:]):  # Show last 10 versions
            timestamp = datetime.fromtimestamp(version["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            version_data.append({
                "Version": version["version"],
                "Date": timestamp,
                "Author": version.get("author", "Unknown"),
                "Changes": len(version.get("changes", [])),
                "Summary": ", ".join(version.get("changes", [])[:2])
            })

        st.dataframe(version_data, use_container_width=True)

        # Version comparison
        if len(versions) >= 2:
            st.markdown("##### 🔍 Version Comparison")
            col1, col2, col3 = st.columns(3)

            with col1:
                version1 = st.selectbox("Compare From", [v["version"] for v in versions])

            with col2:
                version2 = st.selectbox("Compare To", [v["version"] for v in versions], index=min(1, len(versions)-1))

            with col3:
                if st.button("🔍 Compare Versions"):
                    diff = config_manager.get_configuration_diff(version1, version2)

                    if "error" in diff:
                        st.error(f"❌ {diff['error']}")
                    else:
                        st.markdown("**Configuration Differences:**")

                        if diff.get("added"):
                            st.markdown("**Added:**")
                            st.json(diff["added"])

                        if diff.get("modified"):
                            st.markdown("**Modified:**")
                            st.json(diff["modified"])

                        if diff.get("removed"):
                            st.markdown("**Removed:**")
                            st.json(diff["removed"])

                        if not any([diff.get("added"), diff.get("modified"), diff.get("removed")]):
                            st.info("ℹ️ No differences found between selected versions.")


def render_backup_restore():
    """Render backup and restore functionality."""
    st.markdown("#### 💾 Backup & Restore")

    config_manager = get_dynamic_config_manager()

    # Backup section
    st.markdown("##### 📤 Create Backup")

    col1, col2 = st.columns(2)

    with col1:
        backup_name = st.text_input(
            "Backup Name",
            value=f"manual_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            help="Custom name for this backup"
        )

    with col2:
        if st.button("💾 Create Backup", use_container_width=True):
            with st.spinner("Creating configuration backup..."):
                try:
                    import asyncio
                    backup_path = asyncio.run(config_manager.create_backup(backup_name))
                    st.success(f"✅ Backup created successfully!")
                    st.info(f"📁 Backup saved to: {backup_path}")
                except Exception as e:
                    st.error(f"❌ Failed to create backup: {e}")

    # Available backups
    st.markdown("---")
    st.markdown("##### 📂 Available Backups")

    backup_dir = config_manager.backup_dir
    if backup_dir.exists():
        backup_files = list(backup_dir.glob("*.json"))

        if backup_files:
            backup_data = []
            for backup_file in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True):
                try:
                    stat = backup_file.stat()
                    size = stat.st_size / 1024  # KB
                    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

                    # Try to read backup metadata
                    try:
                        with open(backup_file, 'r') as f:
                            backup_content = json.load(f)
                        version = backup_content.get("version", "Unknown")
                    except:
                        version = "Unknown"

                    backup_data.append({
                        "Name": backup_file.stem,
                        "Version": version,
                        "Size (KB)": f"{size:.1f}",
                        "Created": modified,
                        "Path": str(backup_file)
                    })
                except Exception as e:
                    continue

            if backup_data:
                st.dataframe(backup_data[["Name", "Version", "Size (KB)", "Created"]], use_container_width=True)

                # Restore section
                st.markdown("---")
                st.markdown("##### 📥 Restore Backup")

                selected_backup = st.selectbox(
                    "Select Backup to Restore",
                    [item["Name"] for item in backup_data],
                    help="Choose a backup to restore"
                )

                if selected_backup:
                    selected_backup_path = next(
                        item["Path"] for item in backup_data
                        if item["Name"] == selected_backup
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("🔍 Preview Backup", use_container_width=True):
                            try:
                                with open(selected_backup_path, 'r') as f:
                                    backup_content = json.load(f)

                                st.markdown("**Backup Contents Preview:**")
                                st.json(backup_content.get("config", {}))

                            except Exception as e:
                                st.error(f"❌ Failed to preview backup: {e}")

                    with col2:
                        if st.button("📥 Restore Backup", use_container_width=True, type="primary"):
                            if st.session_state.get(f"confirm_restore_{selected_backup}", False):
                                with st.spinner(f"Restoring backup {selected_backup}..."):
                                    try:
                                        import asyncio
                                        success = asyncio.run(config_manager.restore_backup(selected_backup_path))

                                        if success:
                                            st.success("✅ Backup restored successfully!")
                                            st.info("🔄 Please refresh the page to see restored configuration.")
                                            st.session_state[f"confirm_restore_{selected_backup}"] = False
                                        else:
                                            st.error("❌ Failed to restore backup")

                                    except Exception as e:
                                        st.error(f"❌ Restore failed: {e}")
                            else:
                                st.session_state[f"confirm_restore_{selected_backup}"] = True
                                st.warning("⚠️ Click again to confirm restore. This will overwrite current configuration!")

            else:
                st.info("No backup files found.")
        else:
            st.info("No backup files found.")
    else:
        st.info("Backup directory does not exist.")


def render_configuration_templates():
    """Render configuration templates management."""
    st.markdown("#### 📄 Configuration Templates")

    config_manager = get_dynamic_config_manager()
    templates = config_manager.get_available_templates()

    if not templates:
        st.info("No configuration templates available.")
        return

    # Template selection
    st.markdown("##### 📋 Available Templates")

    for template_name, template in templates.items():
        with st.expander(f"📄 {template_name}"):
            st.markdown(f"**Description:** {template.description}")

            # Show template structure
            st.markdown("**Template Structure:**")
            st.json(template.template_data)

            # Template variables
            if template.variables:
                st.markdown("**Template Variables:**")
                for var_name, var_desc in template.variables.items():
                    st.markdown(f"- `{{{var_name}}}`: {var_desc}")

            # Required fields
            if template.required_fields:
                st.markdown("**Required Fields:**")
                for field in template.required_fields:
                    st.markdown(f"- {field}")

    # Template usage
    st.markdown("---")
    st.markdown("##### 🛠️ Create from Template")

    selected_template = st.selectbox("Select Template", list(templates.keys()))

    if selected_template:
        template = templates[selected_template]

        st.markdown(f"Creating configuration from template: **{selected_template}**")

        # Template variable inputs
        template_vars = {}
        if template.variables:
            st.markdown("**Fill Template Variables:**")

            for var_name, var_desc in template.variables.items():
                template_vars[var_name] = st.text_input(
                    f"{var_name}",
                    help=var_desc,
                    key=f"template_var_{var_name}"
                )

        # Generate configuration from template
        if st.button("🔨 Generate Configuration"):
            try:
                # Simple template variable substitution
                template_str = json.dumps(template.template_data)

                for var_name, var_value in template_vars.items():
                    template_str = template_str.replace(f"{{{{{var_name}}}}}", str(var_value))

                generated_config = json.loads(template_str)

                st.markdown("**Generated Configuration:**")
                st.json(generated_config)

                # Option to apply generated configuration
                if st.button("✅ Apply Generated Configuration"):
                    try:
                        # Apply to current configuration
                        current_config = config_manager.get_current_configuration()

                        # Merge generated config (simple merge)
                        if "agents" in generated_config:
                            if "agents" not in current_config:
                                current_config["agents"] = {}
                            current_config["agents"].update(generated_config["agents"])

                        # Validate and save
                        import asyncio
                        validation_result = asyncio.run(config_manager.validate_configuration(current_config))

                        if validation_result["valid"]:
                            asyncio.run(config_manager.save_configuration())
                            st.success("✅ Template configuration applied successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Generated configuration is invalid")
                            for error in validation_result["errors"]:
                                st.error(f"• {error}")

                    except Exception as e:
                        st.error(f"❌ Failed to apply template: {e}")

            except Exception as e:
                st.error(f"❌ Failed to generate configuration: {e}")