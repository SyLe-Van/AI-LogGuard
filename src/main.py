import click
from fetchers import JenkinsFetcher, GitLabFetcher  # Sẽ viết ở bước 3
from parser import parse_with_regex as basic_parse  # Sẽ viết ở bước 4

@click.group()
def cli():
    """AI-LogGuard: Cross-platform CI/CD tools for multiple environments."""
    pass

@cli.command()
@click.option('--provider', required=True, type=click.Choice(['jenkins', 'gitlab']), help='CI/CD provider (jenkins or gitlab)')
@click.option('--url', required=True, help='Base URL of the CI/CD instance (e.g., http://localhost:8080)')
@click.option('--job-id', required=True, help='Job or build ID (e.g., myjob for Jenkins, project_id:job_id for GitLab)')
@click.option('--token', required=True, help='API token for authentication')
def fetch(provider, url, job_id, token):
    """Fetch and summarize CI/CD logs."""
    try:
        # Khởi tạo fetcher dựa trên provider
        if provider == 'jenkins':
            fetcher = JenkinsFetcher(url, token)
        elif provider == 'gitlab':
            fetcher = GitLabFetcher(url, token)
        else:
            click.echo(f"Unsupported provider: {provider}", err=True)
            raise click.Abort()

        # Fetch logs
        click.echo(f"Fetching logs from {provider} job {job_id}...")
        logs = fetcher.get_logs(job_id)

        # Parse logs
        click.echo("Parsing logs...")
        summary = basic_parse(logs, r'.*')  # Sử dụng regex đơn giản cho ví dụ
        click.echo(summary)

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    cli()
