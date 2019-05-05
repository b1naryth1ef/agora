#!/usr/bin/env python3.7

import os
import json
import requests
import asyncio

import websockets
import click
from nacl.encoding import Base64Encoder
from nacl.signing import SigningKey

url = os.getenv('CHAT_URL')
token = os.getenv('CHAT_TOKEN')
identity_key = None


@click.group()
@click.pass_context
def cli(ctx):
    global identity_key

    if not os.path.exists('.identity'):
        print('No existing identity, creating a new one for you...')
        identity_key = SigningKey.generate()

        with open('.identity', 'w') as f:
            json.dump({
                'signing_key': identity_key.encode(encoder=Base64Encoder).decode('utf-8'),
                'verify_key': identity_key.verify_key.encode(encoder=Base64Encoder).decode('utf-8'),
            }, f)
    else:
        with open('.identity', 'r') as f:
            data = json.load(f)
            identity_key = SigningKey(data['signing_key'], encoder=Base64Encoder)


@cli.command('join')
def command_join():
    key = identity_key.verify_key.encode(encoder=Base64Encoder).decode('utf-8')

    r = requests.get(url + '/auth/challenge', params={
        'key': key,
    })
    r.raise_for_status()

    body = json.dumps({
        'key': key,
        'challenge': r.json()['challenge'],
        'identity': {
            'alias': 'testuser',
        }
    })

    signature = Base64Encoder.encode(identity_key.sign(body.encode('utf-8')).signature)

    r = requests.post(url + '/auth/join', headers={
        'Content-Type': 'application/json',
        'X-Challenge-Signature': signature.decode('utf-8'),
    }, data=body)
    if not r.status_code == 200:
        print('Error: {}'.format(r.json()))
        return

    print(r.json())


@cli.command('whoami')
def command_whoami():
    r = requests.get(url + '/identity/@me', headers={
        'Authentication': f'Token {token}'
    })
    print(r.json())


@cli.group()
def realm():
    pass


@realm.command('create')
@click.argument('name')
@click.option('--public/--no-public', default=True)
def command_realm_create(name, public):
    r = requests.post(url + '/realm', headers={
        'Authentication': f'Token {token}'
    }, json={
        'public': public,
        'name': name,
    })
    print(r.json())


@realm.group()
def channel():
    pass


@channel.command('create')
@click.argument('realm_id')
@click.argument('name')
@click.option('--topic', default='')
@click.option('--type', default='realm_text')
def command_realm_channel_create(realm_id, name, topic, type):
    r = requests.post(url + f'/realm/{realm_id}/channel', headers={
        'Authentication': f'Token {token}'
    }, json={
        'type': type,
        'name': name,
        'topic': topic,
    })
    print(r.json())


@channel.command('delete')
@click.argument('realm_id')
@click.argument('channel_id')
def command_realm_channel_delete(realm_id, channel_id):
    r = requests.delete(url + f'/realm/{realm_id}/channel/{channel_id}', headers={
        'Authentication': f'Token {token}'
    })
    r.raise_for_status()


@cli.command('stream')
def command_stream():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_stream_coro())


async def _stream_coro():
    wsurl = url.replace('https', 'wss').replace('http', 'ws')
    conn = websockets.connect(
        wsurl + '/stream/ws',
        extra_headers={
            'Authentication': f'Token {token}'
        }
    )

    async with conn as websocket:
        while True:
            print(await websocket.recv())

if __name__ == '__main__':
    cli(obj={})
