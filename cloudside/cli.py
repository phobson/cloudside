import click

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(x):
        return x

from cloudside import asos, hydra


@click.group()
def main():
    pass


@main.command()
@click.argument('station')
@click.argument('startdate')
@click.argument('enddate')
@click.argument('email')
@click.option('--folder')
@click.option('--force', is_flag=True)
def get_asos(station, startdate, enddate, email, folder, force):
    folder = '.' or folder
    return asos.get_data(station, startdate, enddate, email, folder=folder,
                         force_download=force, pbar_fxn=tqdm)


@main.command()
@click.argument('station')
@click.option('--folder')
@click.option('--force', is_flag=True)
def get_hydra(station, folder, force):
    folder = '.' or folder
    return hydra.get_data(station, folder=folder, force_download=force)
