import time
from pyaimp import Client, PlayBackState
from pycaw.pycaw import AudioUtilities, IAudioMeterInformation

# Constant for the AIMP executable name
AIMP_EXE = 'AIMP.exe'
# List to keep track of the last command sent to avoid redundant actions
sent_commands = ['play']


def get_audio_sessions() -> list:
    """Retrieve all audio sessions that have an associated process"""
    sessions = AudioUtilities.GetAllSessions()
    # Filter sessions to include only those with an associated process
    return [session for session in sessions if session.Process]


def is_peak_value_exist(session) -> bool:
    """Check if the audio session is producing any significant sound"""

    # Query the IAudioMeterInformation interface for peak audio value
    volume = session._ctl.QueryInterface(IAudioMeterInformation)
    peak = volume.GetPeakValue()

    # If the peak value is greater than the threshold, consider it as active
    return peak > 0.00001


def get_active_sessions() -> list:
    """
    Get a list of process names that are actively producing audio.
    
    Returns:
        List of process names with active audio output.
    """
    sessions = get_audio_sessions()
    active_sessions = []

    for session in sessions:
        if is_peak_value_exist(session):
            active_sessions.append(session.Process.name())

    return active_sessions


def control_aimp():
    """
    Control AIMP playback based on other active audio sessions.
    
    If AIMP is playing and other processes are producing audio, pause AIMP.
    If AIMP is paused (by this script) and no other audio is active, resume playback.
    """
    active_sessions = get_active_sessions()

    # Remove AIMP's own process from the active sessions list if present
    try:
        active_sessions.remove(AIMP_EXE)
    except ValueError:
        pass

    try:
        # Create a client instance for AIMP control
        client = Client()
        state = client.get_playback_state()

        # If AIMP is playing and there are other active audio sessions, pause playback.
        if state == PlayBackState.Playing:
            if active_sessions:
                client.pause()
                sent_commands.append('pause')
        # If AIMP is not playing and it was paused by this script, resume playback when no other audio is active.
        elif state != PlayBackState.Playing and sent_commands[-1] == 'pause':
            if not active_sessions:
                client.play()
                sent_commands.append('play')
    except RuntimeError:
        # In case of errors with AIMP client operations, do nothing.
        pass


def main():
    """Main loop that continuously checks active audio sessions and controls AIMP playback"""
    while True:
        control_aimp()
        # Delay between checks; lower this value for faster response at the expense of higher CPU usage.
        time.sleep(1)


if __name__ == "__main__":
    main()
    # This sleep is redundant because main() has an infinite loop, but kept for safety.
    time.sleep(100)
