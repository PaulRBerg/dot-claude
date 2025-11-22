#!/usr/bin/env python3
"""
cc-notifier CLI - Command-line interface for managing cc-notifier.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

import click
from loguru import logger
from tabulate import tabulate

from hooks.cc_notifier.config import Config
from hooks.cc_notifier.config_loader import ConfigLoader, DEFAULT_CONFIG_PATH, DEFAULT_EXPORT_DIR
from hooks.cc_notifier.database import SessionTracker
from hooks.cc_notifier.notifier import MacNotifier
from hooks.cc_notifier.utils import format_duration, setup_logging


@click.group()
@click.version_option(version="1.0.0", prog_name="cc-notifier")
def cli():
    """cc-notifier - Notification hook for Claude Code."""
    setup_logging()


@cli.group()
def config():
    """Manage cc-notifier configuration."""
    pass


@config.command("show")
@click.option(
    "--path",
    type=click.Path(exists=True, path_type=Path),
    help="Custom config file path"
)
def config_show(path):
    """Show current configuration."""
    try:
        loader = ConfigLoader(path)
        cfg = loader.load()

        # Build configuration table
        config_data = [
            ["Notification Threshold", f"{cfg.notification.threshold_seconds}s"],
            ["Notification Sound", cfg.notification.sound],
            ["App Bundle", cfg.notification.app_bundle],
            ["Database Path", str(cfg.database.path)],
            ["Retention Days", f"{cfg.cleanup.retention_days} days"],
            ["Auto-cleanup Enabled", "Yes" if cfg.cleanup.auto_cleanup_enabled else "No"],
            ["Export Before Cleanup", "Yes" if cfg.cleanup.export_before_cleanup else "No"],
            ["Log Level", cfg.logging.level],
            ["Log Path", str(cfg.logging.path)],
        ]

        click.echo("\n" + click.style("Current Configuration:", bold=True))
        click.echo(tabulate(config_data, headers=["Setting", "Value"], tablefmt="simple"))
        click.echo(f"\nConfig file: {loader.config_path}")

        if not loader.config_path.exists():
            click.echo(click.style("\nNote: Using default configuration (no config file found)", fg="yellow"))

    except Exception as e:
        click.echo(click.style(f"Error loading configuration: {e}", fg="red"), err=True)
        sys.exit(1)


@config.command("edit")
@click.option(
    "--path",
    type=click.Path(path_type=Path),
    help="Custom config file path"
)
def config_edit(path):
    """Edit configuration file in $EDITOR."""
    try:
        loader = ConfigLoader(path)
        config_path = loader.config_path

        # Create config file if it doesn't exist
        if not config_path.exists():
            click.echo(f"Creating new config file at {config_path}...")
            loader.save(loader.load())

        # Get editor from environment
        editor = subprocess.os.getenv("EDITOR", "vi")

        # Open editor
        click.echo(f"Opening {config_path} in {editor}...")
        subprocess.run([editor, str(config_path)])

        # Validate after editing
        try:
            cfg = loader.load()
            click.echo(click.style("✓ Configuration is valid", fg="green"))
        except Exception as e:
            click.echo(click.style(f"⚠ Warning: Configuration validation failed: {e}", fg="yellow"))

    except Exception as e:
        click.echo(click.style(f"Error editing configuration: {e}", fg="red"), err=True)
        sys.exit(1)


@config.command("reset")
@click.option(
    "--path",
    type=click.Path(path_type=Path),
    help="Custom config file path"
)
@click.confirmation_option(prompt="Are you sure you want to reset configuration to defaults?")
def config_reset(path):
    """Reset configuration to defaults."""
    try:
        loader = ConfigLoader(path)
        loader.reset_to_defaults()
        click.echo(click.style(f"✓ Configuration reset to defaults: {loader.config_path}", fg="green"))
    except Exception as e:
        click.echo(click.style(f"Error resetting configuration: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
def test():
    """Test notification system."""
    try:
        click.echo("Sending test notification...")

        notifier = MacNotifier()
        notifier.notify_job_done(
            project_name="cc-notifier-test",
            job_number=99,
            duration_str="1m 23s"
        )

        click.echo(click.style("✓ Test notification sent successfully", fg="green"))
        click.echo("\nIf you didn't see a notification, check:")
        click.echo("  1. System notification permissions")
        click.echo("  2. Do Not Disturb mode")
        click.echo("  3. Log file for errors")

    except Exception as e:
        click.echo(click.style(f"✗ Test notification failed: {e}", fg="red"), err=True)
        logger.exception("Test notification failed")
        sys.exit(1)


@cli.command()
@click.option(
    "--days",
    type=int,
    help="Days of data to retain (default: from config)"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without actually deleting"
)
@click.option(
    "--no-export",
    is_flag=True,
    help="Skip exporting data before cleanup"
)
def cleanup(days, dry_run, no_export):
    """Clean up old session data."""
    try:
        # Load config
        loader = ConfigLoader()
        cfg = loader.load()
        retention_days = days if days is not None else cfg.cleanup.retention_days
        export_before = not no_export and cfg.cleanup.export_before_cleanup

        # Get tracker
        tracker = SessionTracker()

        if dry_run:
            # Count sessions that would be deleted
            from datetime import datetime, timedelta
            cutoff_timestamp = int((datetime.now() - timedelta(days=retention_days)).timestamp())

            with tracker._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM sessions WHERE created_at < ?",
                    (cutoff_timestamp,)
                )
                count = cursor.fetchone()[0]

            click.echo(f"\n{click.style('DRY RUN MODE', bold=True)} - No data will be deleted\n")
            click.echo(f"Retention period: {retention_days} days")
            click.echo(f"Sessions to delete: {count}")
            click.echo(f"Export before cleanup: {'Yes' if export_before else 'No'}")
            sys.exit(0)

        # Confirm cleanup
        click.echo(f"\nRetention period: {retention_days} days")
        click.echo(f"Export before cleanup: {'Yes' if export_before else 'No'}")

        if not click.confirm("\nProceed with cleanup?"):
            click.echo("Cleanup cancelled")
            sys.exit(0)

        # Run cleanup
        click.echo("\nRunning cleanup...")
        stats = tracker.cleanup_old_data(
            retention_days=retention_days,
            export_before=export_before
        )

        # Display results
        click.echo(click.style("\n✓ Cleanup complete:", fg="green"))
        results = [
            ["Sessions deleted", stats['rows_deleted']],
            ["Space freed", f"{stats['space_freed_kb']} KB"],
        ]

        if export_before:
            results.append(["Sessions exported", stats['rows_exported']])
            if stats['rows_exported'] > 0:
                click.echo(f"\nExported data saved to: {DEFAULT_EXPORT_DIR}")

        click.echo(tabulate(results, tablefmt="simple"))

    except Exception as e:
        click.echo(click.style(f"✗ Cleanup failed: {e}", fg="red"), err=True)
        logger.exception("Cleanup failed")
        sys.exit(1)


if __name__ == "__main__":
    cli()
