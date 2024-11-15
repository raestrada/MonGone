import click
from mongone.cmd.commands import cli, init, generate_report
from mongone.utils.helpers import Console

console = Console()

# Añadir los comandos al CLI
console.print("[INFO] Adding commands to the CLI...", style="bold blue")
cli.add_command(init)
cli.add_command(generate_report)

if __name__ == "__main__":
    console.print("[INFO] Starting MonGone CLI...", style="bold blue")
    cli()
    console.print("[INFO] MonGone CLI execution finished.", style="bold blue")
