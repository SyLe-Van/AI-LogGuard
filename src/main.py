import click
from fetchers.jenkins_fetcher import JenkinsFetcher
# from fetchers.gitlab_fetcher import GitLabFetcher
from parse import basic_parse

@click.group()
def cli():
    pass

@click.command()
@click.option('--provider', required=True, type=click.Choice(['jenkins']), help='CI/CD provider')
@click.option('--url', required=True, help='Base URL of the CI/CD instance (e.g., http://localhost:8080)')
@click.option('--job-id', required=True, help='Jenkins job name (e.g., my-job)')
@click.option('--token', required=True, help='Jenkins API token')
@click.option('--username', default='admin', help='Jenkins username (default: admin)')
@click.option('--build-number', default='lastBuild', help='Build number or lastBuild (default: lastBuild)')
def fetch(provider, url, job_id, token, username, build_number):
    if not url.startswith(('http://', 'https://')):
        click.echo("Error: URL must start with http:// or https://", err=True)
        return
    if not job_id.strip():
        click.echo("Error: Job ID cannot be empty", err=True)
        return
    if provider != 'jenkins':
        click.echo(f"Provider {provider} not supported yet", err=True)
        return
    
    try:
        fetcher = JenkinsFetcher(url, token, username)
        logs = fetcher.get_logs(job_id, build_number)
        if len(logs) > 10_000_000:
            click.echo("Warning: Logs too large, truncating to 10MB", err=True)
            logs = logs[:10_000_000]
        click.echo(f"Logs fetched successfully (first 500 chars):\n{logs[:500]}...")
        # Gọi parser
        summary = basic_parse(logs, r'.*')
        click.echo(f"Summary:\n{summary}")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

cli.add_command(fetch)

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        with open('tests/sample_logs.txt', 'r') as f:
            logs_text = f.read()
        from parse import basic_parse
        print('Kết quả basic_parse:')
        print(basic_parse(logs_text))

if __name__ == "__main__":
    cli()
