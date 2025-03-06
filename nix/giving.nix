{ lib
, buildPythonPackage
, fetchFromGitHub
, poetry-core
, asttokens
, reactivex
, varname
}:

buildPythonPackage rec {
  pname = "giving";
  version = "0.4.2";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "breuleux";
    repo = "giving";
    rev = "v${version}";
    hash = "sha256-eOgg0TlHSZGAIVIMoAL/tvO7FbYNJuGUB5AhxbzounM=";
  };

  # unpin dependencies
  postPatch = ''
    sed -i -E 's/^(\S+) = "[>^].*"$/\1 = "*"/' pyproject.toml
  '';

  nativeBuildInputs = [
    poetry-core
  ];

  propagatedBuildInputs = [
    asttokens
    reactivex
    varname
  ];

  pythonImportsCheck = [ "giving" ];

  meta = with lib; {
    description = "Reactive logging";
    homepage = "https://github.com/breuleux/giving";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
  };
}
