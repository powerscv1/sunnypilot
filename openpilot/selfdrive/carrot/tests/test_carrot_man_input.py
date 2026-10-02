from openpilot.selfdrive.carrot.carrot_man_input import CARROT_MAN_STALE_SECONDS


def test_carrot_man_stale_timeout_is_bounded():
  assert 0.5 <= CARROT_MAN_STALE_SECONDS <= 3.0
