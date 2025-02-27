{ lib
, python3
, fetchPypi
, fetchFromGitHub
}:

python3.pkgs.buildPythonApplication rec {
  pname = "flask-session2";
  version = "1.3.1";
  #version = "1.3.1.2023.06.12";
  #version = "1.3.1-unstable-2023-06-12";
  format = "pyproject";

  src = fetchPypi {
    pname = "Flask-Session2";
    inherit version;
    hash = "sha256-Fx6YbU4xR5X0SKUnCV5C32q/unbD5M5cjkxhyFfFnLI=";
  };

  /*
  # https://github.com/christopherpickering/flask-session2
  src = fetchFromGitHub {
    owner = "christopherpickering";
    repo = "flask-session2";
    rev = "efc14774e7aa55486ac70e0f3600d25fb762321c";
    sha256 = "sha256-Dpk1P9nK7DeoT868O6C86HrsP0X0VMknt0xOjcF+PA4=";
  };
  */

  # fix: ERROR: Could not find a version that satisfies the requirement cachelib<0.10.0,>=0.9.0
  # a: cachelib = "^0.9.0"
  # b: cachelib = "*"
  postPatch = ''
    sed -i -E 's/= "\^[^"]+"/= "*"/' pyproject.toml
  '';

  nativeBuildInputs = [
    python3.pkgs.poetry-core
  ];

  propagatedBuildInputs = with python3.pkgs; [
    cachelib
    flask
    pytz
  ];

  pythonImportsCheck = [ "flask_session" ];

  meta = with lib; {
    description = "Adds server-side session support to your Flask application";
    #homepage = "https://pypi.org/project/flask-session2";
    homepage = "https://github.com/christopherpickering/flask-session2";
    license = with licenses; [ bsd3 bsd2 ];
    maintainers = with maintainers; [ ];
  };
}
