{
  description = "FestEngine development environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

  outputs = { self, nixpkgs }:
    let
      forLinux = nixpkgs.lib.genAttrs [ "x86_64-linux" "aarch64-linux" ];
    in {
      packages = forLinux (system: {
        python = nixpkgs.legacyPackages.${system}.python3.withPackages (ps: [
          ps.debugpy
          ps.wxpython
          ps.python-vlc
        ]);
      });

      devShells = forLinux (system: let pkgs = nixpkgs.legacyPackages.${system}; in {
        default = pkgs.mkShell {
          packages = [ self.packages.${system}.python pkgs.vlc pkgs.gettext ];
        };
      });
    };
}