{ lib
, buildPythonPackage
, fetchFromGitHub
, poetry-core
}:

buildPythonPackage rec {
  pname = "ovld";
  version = "0.3.5";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "breuleux";
    repo = "ovld";
    rev = "v${version}";
    hash = "sha256-2s24I6CMldGJjneRFYuHTUAjdd+q//ABWiS8vR9pW1s=";
  };

  nativeBuildInputs = [
    poetry-core
  ];

  pythonImportsCheck = [ "ovld" ];

  meta = with lib; {
    description = "Advanced multiple dispatch for Python functions";
    homepage = "https://github.com/breuleux/ovld";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
  };
}
