{ lib
, buildPythonPackage
, fetchFromGitHub
, poetry-core
}:

buildPythonPackage rec {
  pname = "codefind";
  version = "0.1.6";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "breuleux";
    repo = "codefind";
    rev = "v${version}";
    hash = "sha256-jSAOlxHpi9hjRJjfj9lBpbgyEdiBCI7vVZ/RXspPbgc=";
  };

  nativeBuildInputs = [
    poetry-core
  ];

  pythonImportsCheck = [ "codefind" ];

  meta = with lib; {
    description = "Find code objects and their referents";
    homepage = "https://github.com/breuleux/codefind";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
  };
}
