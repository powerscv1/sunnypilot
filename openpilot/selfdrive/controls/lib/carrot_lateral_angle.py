"""Carrot-compatible angle lateral policy."""


class CarrotLateralAnglePolicy:
  """Apply carrot's driver-override behavior to an angle command."""

  @staticmethod
  def desired_angle(model_angle_deg: float, measured_angle_deg: float, steering_pressed: bool) -> float:
    return float(measured_angle_deg if steering_pressed else model_angle_deg)

