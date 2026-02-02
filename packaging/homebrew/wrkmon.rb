class Wrkmon < Formula
  include Language::Python::Virtualenv

  desc "Stealth TUI YouTube audio player - stream music while looking productive"
  homepage "https://github.com/Umar-Khan-Yousafzai/Wrkmon-TUI-Youtube"
  url "https://files.pythonhosted.org/packages/source/w/wrkmon/wrkmon-1.1.0.tar.gz"
  sha256 "REPLACE_WITH_ACTUAL_SHA256_AFTER_PYPI_UPLOAD"
  license "MIT"

  depends_on "python@3.11"
  depends_on "mpv"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "wrkmon", shell_output("#{bin}/wrkmon --version")
  end
end
