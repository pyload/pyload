{ lib
, buildPythonPackage
, fetchFromGitHub
, poetry-core
, blessed
, codefind
, ovld
, watchdog
, giving
, rich
}:

buildPythonPackage rec {
  pname = "jurigged";
  version = "0.5.8";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "breuleux";
    repo = "jurigged";
    rev = "v${version}";
    hash = "sha256-XlImCnBpr/PjqEPFIpQfe1fWZcbM1btupikz2ab0vyI=";
  };

  nativeBuildInputs = [
    poetry-core
  ];

  propagatedBuildInputs = [
    blessed
    codefind
    ovld
    watchdog
  ];

  passthru.optional-dependencies = {
    develoop = [
      giving
      rich
    ];
  };

  pythonImportsCheck = [ "jurigged" ];

  meta = with lib; {
    description = "Hot reloading for Python";
    homepage = "https://github.com/breuleux/jurigged";
    changelog = "https://github.com/breuleux/jurigged/blob/${src.rev}/CHANGELOG.md";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
  };
}
