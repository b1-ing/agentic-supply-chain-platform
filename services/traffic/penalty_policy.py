# services/traffic/penalty_policy.py

from dataclasses import dataclass


@dataclass(frozen=True)
class Penalty:
    #
    # Additional delay (seconds)
    #
    delay_seconds: float

    #
    # Radius of influence (metres)
    #
    radius_m: float

    #
    # Whether the road should be considered closed
    #
    close_road: bool = False

    #
    # Multiplier cap
    #
    max_multiplier: float = 3.0


class PenaltyPolicy:
    """
    Determines how different traffic incidents should affect routing.

    This service is deterministic.

    It should never modify the graph directly.
    """

    ####################################################################
    # Limits
    ####################################################################

    #
    # Never allow travel time to exceed this multiple
    # of the free-flow travel time.
    #
    MAX_MULTIPLIER = 3.0

    #
    # Maximum additional delay (30 minutes)
    #
    MAX_DELAY_SECONDS = 1800

    ####################################################################
    # Public
    ####################################################################

    def penalty(self, incident) -> Penalty:

        incident_type = incident.incident_type.lower()

        severity = incident.analysis.severity

        ###############################################################

        if incident_type == "accident":
            return Penalty(
                delay_seconds=self._scale(
                    severity,
                    120,
                    900,
                ),
                radius_m=self._scale(
                    severity,
                    50,
                    300,
                ),
            )

        ###############################################################

        if incident_type == "congestion":
            return Penalty(
                delay_seconds=self._scale(
                    severity,
                    60,
                    600,
                ),
                radius_m=self._scale(
                    severity,
                    100,
                    500,
                ),
            )

        ###############################################################

        if incident_type == "roadworks":
            return Penalty(
                delay_seconds=self._scale(
                    severity,
                    90,
                    480,
                ),
                radius_m=self._scale(
                    severity,
                    100,
                    400,
                ),
            )

        ###############################################################

        if incident_type == "closure":
            return Penalty(
                delay_seconds=self.MAX_DELAY_SECONDS,
                radius_m=25,
                close_road=True,
            )

        ###############################################################

        if incident_type == "flood":
            return Penalty(
                delay_seconds=self._scale(
                    severity,
                    300,
                    self.MAX_DELAY_SECONDS,
                ),
                radius_m=self._scale(
                    severity,
                    100,
                    600,
                ),
                close_road=severity > 0.9,
            )

        ###############################################################

        #
        # Unknown event
        #

        return Penalty(
            delay_seconds=120,
            radius_m=100,
        )

    ####################################################################
    # Compatibility
    ####################################################################

    def penalty_seconds(
        self,
        incident,
    ) -> float:
        """
        Convenience helper used by TrafficPenaltyService.
        """

        return self.penalty(
            incident,
        ).delay_seconds

    ####################################################################
    # Utilities
    ####################################################################

    def clamp(
        self,
        base_time: float,
        penalty: float,
    ) -> float:
        """
        Clamp a penalty so the travel time never exceeds
        MAX_MULTIPLIER × free-flow travel time.
        """

        max_allowed = min(
            base_time * self.MAX_MULTIPLIER,
            base_time + self.MAX_DELAY_SECONDS,
        )

        return min(
            penalty,
            max_allowed - base_time,
        )

    ####################################################################

    @staticmethod
    def _scale(
        severity: float,
        minimum: float,
        maximum: float,
    ) -> float:

        severity = max(
            0.0,
            min(
                severity,
                1.0,
            ),
        )

        return minimum + severity * (maximum - minimum)
