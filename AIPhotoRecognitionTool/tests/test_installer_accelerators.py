import unittest

from photo_recognition_gui_production import select_torch_install_plan


class TestInstallerAccelerators(unittest.TestCase):
    def test_cuda_prefers_cu121(self):
        plan = select_torch_install_plan("cuda", "win32", has_nvidia=True)
        self.assertEqual(plan["mode"], "cuda")
        self.assertEqual(plan["targets"][0], "cu121")

    def test_auto_with_nvidia(self):
        plan = select_torch_install_plan("auto", "win32", has_nvidia=True)
        self.assertEqual(plan["mode"], "cuda")

    def test_cpu_forced(self):
        plan = select_torch_install_plan("cpu", "win32", has_nvidia=True)
        self.assertEqual(plan["mode"], "cpu")

    def test_amd_windows_directml(self):
        plan = select_torch_install_plan("amd", "win32", has_nvidia=False)
        self.assertEqual(plan["mode"], "amd-directml")

    def test_auto_windows_no_nvidia_prefers_directml(self):
        plan = select_torch_install_plan("auto", "win32", has_nvidia=False)
        self.assertEqual(plan["mode"], "amd-directml")

    def test_amd_linux_rocm(self):
        plan = select_torch_install_plan("amd", "linux", has_nvidia=False)
        self.assertEqual(plan["mode"], "amd-rocm")
        self.assertTrue(any("rocm" in idx for idx in plan["indices"]))

    def test_auto_linux_no_nvidia_prefers_rocm(self):
        plan = select_torch_install_plan("auto", "linux", has_nvidia=False)
        self.assertEqual(plan["mode"], "amd-rocm")


if __name__ == "__main__":
    unittest.main()
