import asyncio
import sys

import onvif


IP = '192.168.0.100'  # Camera IP address
PORT = 10080  # Port
USER = 'admin'  # Username
PASS = 'password'  # Password

XMAX = 1
XMIN = -1
YMAX = 1
YMIN = -1
moverequest = None
ptz = None
active = False


async def do_move(ptz, request):
    # Start continuous move
    global active
    if active:
        await ptz.Stop({'ProfileToken': request.ProfileToken})
    active = True
    await ptz.ContinuousMove(request)


async def move_up(ptz, request):
    print('move up...')
    request.Velocity.PanTilt.x = 0
    request.Velocity.PanTilt.y = YMAX
    await do_move(ptz, request)


async def move_down(ptz, request):
    print('move down...')
    request.Velocity.PanTilt.x = 0
    request.Velocity.PanTilt.y = YMIN
    await do_move(ptz, request)


async def move_right(ptz, request):
    print('move right...')
    request.Velocity.PanTilt.x = XMAX
    request.Velocity.PanTilt.y = 0
    await do_move(ptz, request)


async def move_left(ptz, request):
    print('move left...')
    request.Velocity.PanTilt.x = XMIN
    request.Velocity.PanTilt.y = 0
    await do_move(ptz, request)


async def move_upleft(ptz, request):
    print('move up left...')
    request.Velocity.PanTilt.x = XMIN
    request.Velocity.PanTilt.y = YMAX
    await do_move(ptz, request)


async def move_upright(ptz, request):
    print('move up left...')
    request.Velocity.PanTilt.x = XMAX
    request.Velocity.PanTilt.y = YMAX
    await do_move(ptz, request)


async def move_downleft(ptz, request):
    print('move down left...')
    request.Velocity.PanTilt.x = XMIN
    request.Velocity.PanTilt.y = YMIN
    await do_move(ptz, request)


async def move_downright(ptz, request):
    print('move down left...')
    request.Velocity.PanTilt.x = XMAX
    request.Velocity.PanTilt.y = YMIN
    await do_move(ptz, request)


async def setup_move():
    mycam = onvif.ONVIFCamera(IP, PORT, USER, PASS)
    await mycam.update_xaddrs()
    # Create media service object
    media = mycam.create_media_service()

    # Create ptz service object
    global ptz
    ptz = mycam.create_ptz_service()

    # Get target profile
    media_profile = await media.GetProfiles()[0]

    # Get PTZ configuration options for getting continuous move range
    request = ptz.create_type('GetConfigurationOptions')
    request.ConfigurationToken = media_profile.PTZConfiguration.token
    ptz_configuration_options = await ptz.GetConfigurationOptions(request)

    global moverequest
    moverequest = ptz.create_type('ContinuousMove')
    moverequest.ProfileToken = media_profile.token
    if moverequest.Velocity is None:
        moverequest.Velocity = await ptz.GetStatus(
            {
                'ProfileToken': media_profile.token,
            },
        ).Position

    # Get range of pan and tilt
    # NOTE: X and Y are velocity vector
    global XMAX, XMIN, YMAX, YMIN
    XMAX = ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].XRange.Max
    XMIN = ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].XRange.Min
    YMAX = ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].YRange.Max
    YMIN = ptz_configuration_options.Spaces.ContinuousPanTiltVelocitySpace[0].YRange.Min


def readin():
    """Reading from stdin and displaying menu."""
    global moverequest, ptz

    selection = sys.stdin.readline().strip('\n')
    lov = [x for x in selection.split(' ') if x != '']
    if lov:
        loop = asyncio.get_event_loop()
        if lov[0].lower() in ['u', 'up']:
            coro = move_up(ptz, moverequest)
        elif lov[0].lower() in ['d', 'do', 'dow', 'down']:
            coro = move_down(ptz, moverequest)
        elif lov[0].lower() in ['l', 'le', 'lef', 'left']:
            coro = move_left(ptz, moverequest)
        elif lov[0].lower() in ['l', 'le', 'lef', 'left']:
            coro = move_left(ptz, moverequest)
        elif lov[0].lower() in ['r', 'ri', 'rig', 'righ', 'right']:
            coro = move_right(ptz, moverequest)
        elif lov[0].lower() in ['ul']:
            coro = move_upleft(ptz, moverequest)
        elif lov[0].lower() in ['ur']:
            coro = move_upright(ptz, moverequest)
        elif lov[0].lower() in ['dl']:
            coro = move_downleft(ptz, moverequest)
        elif lov[0].lower() in ['dr']:
            coro = move_downright(ptz, moverequest)
        elif lov[0].lower() in ['s', 'st', 'sto', 'stop']:
            coro = ptz.Stop({'ProfileToken': moverequest.ProfileToken})
        else:
            print(
                "What are you asking?\tI only know, 'up','down','left','right', "
                "'ul' (up left), \n\t\t\t'ur' (up right), 'dl' (down left), "
                "'dr' (down right) and 'stop'",
            )

    if coro:
        loop.call_soon(coro)
    print('')
    print('Your command: ', end='', flush=True)


if __name__ == '__main__':
    setup_move()
    loop = asyncio.get_event_loop()
    try:
        loop.add_reader(sys.stdin, readin)
        print('Use Ctrl-C to quit')
        print('Your command: ', end='', flush=True)
        loop.run_forever()
    except Exception:
        pass
    finally:
        loop.remove_reader(sys.stdin)
        loop.close()
