# modes/progression_mode_base.py
from abc import ABC, abstractmethod
from .chord_mode_base import ChordModeBase
from screen_handler import clear_screen

class ProgressionModeBase(ChordModeBase, ABC):
    def __init__(self, inport, outport, use_timer, timer_duration, play_progression_before_start, chord_set, use_transitions):
        super().__init__(inport, outport, chord_set)
        self.use_timer = use_timer
        self.timer_duration = timer_duration
        self.play_progression_before_start = play_progression_before_start
        self.use_voice_leading = use_transitions
        self._last_prog_info = None

    @abstractmethod
    def _setup_progressions(self):
        """
        Prepare the list of all possible progressions for this mode.
        This method is called once at the beginning of the run.
        It should populate instance variables that are needed by _get_next_progression_info.
        """
        pass

    @abstractmethod
    def _get_next_progression_info(self):
        """
        Get the details for the next progression to be played.
        This method is called at the beginning of each loop iteration.
        It should return a dictionary containing the arguments for the run_progression method.
        If no more progressions are available, it should return None.
        """
        pass

    def run(self):
        """
        Main loop for progression-based modes.
        This method should not be overridden by subclasses.
        """
        self._setup_progressions()

        while not self.exit_flag:
            # If we are not replaying, get a new progression
            if not self._last_prog_info:
                prog_info = self._get_next_progression_info()
            else:
                prog_info = self._last_prog_info

            if prog_info is None:
                # No more progressions to play
                break

            result = self.run_progression(**prog_info)

            if result == 'exit':
                break
            elif result == 'repeat':
                # Store the current progression to be replayed
                self._last_prog_info = prog_info
                clear_screen()
            else:
                # Clear the stored progression so we get a new one next time
                self._last_prog_info = None

        # End of session: display overall stats
        self.show_overall_stats_and_wait()
