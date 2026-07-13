from minitel_workbench.hardware import setup


def test_detect_ready_when_serial_node_present(monkeypatch):
    monkeypatch.setattr(setup, "serial_node_present", lambda: True)
    monkeypatch.setattr(setup, "usb_ftdi_present", lambda: True)
    monkeypatch.setattr(setup, "driver_active", lambda: True)
    st = setup.detect()
    assert st.state == setup.READY
    assert st.ready


def test_detect_driver_missing_when_usb_but_no_node(monkeypatch):
    monkeypatch.setattr(setup, "serial_node_present", lambda: False)
    monkeypatch.setattr(setup, "usb_ftdi_present", lambda: True)
    monkeypatch.setattr(setup, "driver_active", lambda: False)
    assert setup.detect().state == setup.DRIVER_MISSING


def test_detect_no_adapter(monkeypatch):
    monkeypatch.setattr(setup, "serial_node_present", lambda: False)
    monkeypatch.setattr(setup, "usb_ftdi_present", lambda: False)
    monkeypatch.setattr(setup, "driver_active", lambda: False)
    assert setup.detect().state == setup.NO_ADAPTER


def test_usb_detection_parses_system_profiler(monkeypatch):
    sample = "        FT232R USB UART:\n          Vendor ID: 0x0403  (Future Technology…)\n"
    monkeypatch.setattr(setup, "_run", lambda cmd, timeout=15.0: sample)
    assert setup.usb_ftdi_present() is True
    monkeypatch.setattr(setup, "_run", lambda cmd, timeout=15.0: "USB 3.1 Bus:\n")
    assert setup.usb_ftdi_present() is False


def test_driver_active_parses_systemextensionsctl(monkeypatch):
    active = "*\t*\t658CPPCMJJ\tcom.ftdi.vcp.dext (1.6/0)\tNullDriver\t[activated enabled]\n"
    monkeypatch.setattr(setup, "_run", lambda cmd, timeout=15.0: active)
    assert setup.driver_active() is True
    monkeypatch.setattr(setup, "_run", lambda cmd, timeout=15.0: "no extensions\n")
    assert setup.driver_active() is False


def test_guidance_driver_missing_mentions_install_and_approval():
    st = setup.SetupState(
        setup.DRIVER_MISSING, usb_present=True, driver_active=False, serial_node=False
    )
    text = "\n".join(
        setup.guidance(st, installer="/Users/x/Downloads/FTDIUSBSerialVCPDextInstaller.app")
    )
    assert "Install FTDI USB Serial Dext VCP" in text
    assert "Privacy & Security" in text
    assert "FTDIUSBSerialVCPDextInstaller.app" in text


def test_guidance_no_adapter_is_reassuring_for_phone_users():
    st = setup.SetupState(
        setup.NO_ADAPTER, usb_present=False, driver_active=False, serial_node=False
    )
    text = "\n".join(setup.guidance(st, None))
    assert "telephone" in text.lower()
