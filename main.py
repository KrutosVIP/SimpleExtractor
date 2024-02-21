import sys, os, gzip

CompressedModByteHeader = ("SimplePlanes".replace(" ", "") + "CompressedModFileV001").encode()

class ModHeader:
    def __init__(self, windowsOffset=0, macOSOffset=0, linuxOffset=0, androidOffset=0, iOSOffset=0):
        self._HeaderTagV1 = "SimplePlanes".replace(" ", "") + "ModHeaderV001"
        self._HeaderTagV1Bytes = self._HeaderTagV1.encode()

        self.AssetBundleOffsetWindows = windowsOffset
        self.AssetBundleOffsetMacOS = macOSOffset
        self.AssetBundleOffsetLinux = linuxOffset
        self.AssetBundleOffsetAndroid = androidOffset
        self.AssetBundleOffsetIOS = None # There's no iOS support.

    def Read(self, filePath):
        if os.path.exists(filePath):
            if os.path.getsize(filePath) <= len(self._HeaderTagV1Bytes):
                return None
        
        fileStream = open(filePath, "br")
        
        buffer = fileStream.read(len(self._HeaderTagV1Bytes))
        if buffer != self._HeaderTagV1Bytes:
            return None
        
        self.AssetBundleOffsetWindows = self.ReadOffset(fileStream)
        self.AssetBundleOffsetMacOS = self.ReadOffset(fileStream)
        self.AssetBundleOffsetLinux = self.ReadOffset(fileStream)
        self.AssetBundleOffsetAndroid = self.ReadOffset(fileStream)

        fileStream.close()
        return True
    
    def ReadOffset(self, fileStream):
        value = fileStream.read(8)
        num2 = int.from_bytes(value, byteorder='little', signed=True)
        return num2 if (num2 > 0) else -1 # Non-existent

class ModManager:
    def IsCompressed(modPath):
        if os.path.exists(modPath):
            if os.path.getsize(modPath) <= len(CompressedModByteHeader):
                return False
        
        with open(modPath, "br") as file:
            buffer = file.read(len(CompressedModByteHeader))
        
        if buffer != CompressedModByteHeader:
            return False
        
        return True

    def DecompressMod(modPath):
        if os.path.exists(modPath):
            if os.path.getsize(modPath) <= len(CompressedModByteHeader):
                return
        
        with open(modPath, "br") as file:
            buffer = file.read(len(CompressedModByteHeader))
        
        if buffer != CompressedModByteHeader:
            return False
    
        # Original ModTools - decompresses mod on import into game
        text = modPath + ".temp"
        
        # Remove header
        with open(modPath, "rb") as file:
            with open(text, "wb") as temp:
                file.seek(len(CompressedModByteHeader))
                temp.write(file.read())
        
        # Open in streaming mode
        decompressed = modPath + ".decompressed"
        with open(decompressed, "wb") as out:
            with gzip.open(text) as val:
                while True:
                    chunk = val.read(8096)

                    if not chunk:
                        break

                    out.write(chunk)
        
        # Remove temporary
        os.remove(text)

        return True

    def LoadAssetBundleFromMod(modFilePath, out):
        header = ModHeader()

        # TODO: Implement BundledMods?

        # TODO: Also Implement support of old mods (those having no proper header, supposedly)
        header.Read(modFilePath)

        offsets = sorted({"android": header.AssetBundleOffsetAndroid, 
                   "windows": header.AssetBundleOffsetWindows, 
                   "linux": header.AssetBundleOffsetLinux, 
                   "macos": header.AssetBundleOffsetMacOS
                   }.items(), key=lambda _: _[1])
        
        for _ in range(0, len(offsets)):
            # Skip, if offset is -1 (non-existent bundle)
            if offsets[_][1] == -1: continue

            start = offsets[_][1]
            end = offsets[_+1][1] if _+1 < len(offsets) else -1 # Read to the end

            if end == -1:
                length = -1
            else:
                length = end - start
            
            fileStream = open(modFilePath, "rb")
            fileStream.seek(start)

            os.makedirs(out, exist_ok=True)
            with open(os.path.join(out, f"{offsets[_][0]}.assetBundle"), "wb") as f: 
                f.write(fileStream.read(length))

def main():
    if len(sys.argv) <= 1:
        print(f"usage: {sys.argv[0]} <mod files>\n\nUnpack .spmod/.sr2-mod files into unitybundles and data, right into current working directory")
        return
    args = sys.argv[1:]

    for file in args:
        if not os.path.isfile(file):
            print(f"[WARNING] File {file} doesn't exist.")
            continue

        out = ".".join(os.path.basename(file).split(".")[:-1]) + ".extracted" # Output dir

        if ModManager.IsCompressed(file):
            if not ModManager.DecompressMod(file):
                print(f"[ERROR] File {file} is corrupted/not a mod file.")
                return
            # Process decompressed one instead
            file += ".decompressed"

        ModManager.LoadAssetBundleFromMod(file, out)

        if file.endswith(".decompressed"): os.remove(file) # Remove decompressed temp file
            


if __name__ == "__main__": main()