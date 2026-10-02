from openpilot.selfdrive.controls.lib.carrot_lateral_angle import CarrotLateralAnglePolicy


def test_driver_override_uses_measured_angle():
  assert CarrotLateralAnglePolicy.desired_angle(12.0, -3.5, True) == -3.5


def test_without_driver_override_uses_model_angle():
  assert CarrotLateralAnglePolicy.desired_angle(12.0, -3.5, False) == 12.0
