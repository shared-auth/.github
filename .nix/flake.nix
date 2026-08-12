{
  description = "shared-auth organization policy environment with ores-sops";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    ores-sops.url = "github:ORESoftware/ores-sops";
  };
  outputs = { self, nixpkgs, ores-sops, ... }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      eachSystem = nixpkgs.lib.genAttrs systems;
    in {
      devShells = eachSystem (system:
        let pkgs = import nixpkgs { inherit system; };
        in {
          default = pkgs.mkShell {
            packages = (with pkgs; [ git jq python3 just sops age ])
              ++ [ ores-sops.packages.${system}.default ];
            shellHook = ''
              echo "shared-auth organization policy environment"
              ${ores-sops.lib.shellHook}
            '';
          };
        });
    };
}
