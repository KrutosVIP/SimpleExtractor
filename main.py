import sys, os, gzip

SP_CompressedModByteHeader = ("SimplePlanes".replace(" ", "") + "CompressedModFileV001").encode()
SR_CompressedModByteHeader = ("SimpleRockets 2".replace(" ", "") + "CompressedModFileV001").encode()

AssemblyHeader = [72, 50, 210, 183, 136, 156, 218, 76, 148, 225,
        133, 206, 41, 37, 231, 56, 85, 34, 189, 42,
        255, 102, 89, 65, 144, 154, 44, 155, 116, 249,
        4, 176, 253, 60, 223, 206, 149, 88, 214, 65,
        180, 144, 141, 22, 148, 219, 204, 184, 199, 5,
        69, 174, 76, 35, 238, 77, 185, 3, 56, 74,
        142, 193, 9, 65, 166, 111, 44, 77, 95, 65,
        79, 71, 188, 40, 188, 74, 94, 34, 43, 127,
        122, 70, 159, 84, 29, 139, 76, 71, 173, 99,
        166, 201, 165, 205, 200, 157, 191, 124, 138, 64,
        69, 121, 186, 75, 145, 119, 219, 96, 77, 237,
        179, 167, 122, 86, 210, 234, 196, 136, 75, 74,
        189, 217, 66, 223, 138, 211, 169, 229]

class ModHeader:
    def __init__(self, windowsOffset=0, macOSOffset=0, linuxOffset=0, androidOffset=0, iOSOffset=0):
        self._SP_HeaderTagV1 = "SimplePlanes".replace(" ", "") + "ModHeaderV001"
        self._SR_HeaderTagV1 = "SimpleRockets 2".replace(" ", "") + "ModHeaderV001"
        self._SP_HeaderTagV1Bytes = self._SP_HeaderTagV1.encode()
        self._SR_HeaderTagV1Bytes = self._SR_HeaderTagV1.encode()

        self.AssetBundleOffsetWindows = windowsOffset
        self.AssetBundleOffsetMacOS = macOSOffset
        self.AssetBundleOffsetLinux = linuxOffset
        self.AssetBundleOffsetAndroid = androidOffset
        self.AssetBundleOffsetIOS = None # There's no iOS support.

    def DetectModHeader(self, filePath):
        if os.path.exists(filePath):
            if os.path.getsize(filePath) <= len(self._SR_HeaderTagV1Bytes):
                return None
        
        with open(filePath, "br") as file:
            buffer = file.read(len(self._SP_HeaderTagV1Bytes))
        
        if buffer == self._SP_HeaderTagV1Bytes:
            return self._SP_HeaderTagV1Bytes
        
        with open(filePath, "br") as file:
            buffer = file.read(len(self._SR_HeaderTagV1Bytes))
        
        if buffer == self._SR_HeaderTagV1Bytes:
            return self._SR_HeaderTagV1Bytes
        
        return None

    def Read(self, filePath):
        HeaderTagBytes = self.DetectModHeader(filePath)
        if not HeaderTagBytes: return None
        
        fileStream = open(filePath, "br")
        
        buffer = fileStream.read(len(HeaderTagBytes))
        if buffer != HeaderTagBytes:
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
    def detectCompressedHeader(modPath):
        if os.path.exists(modPath):
            if os.path.getsize(modPath) <= len(SR_CompressedModByteHeader):
                return (False, None)
        
        with open(modPath, "br") as file:
            buffer = file.read(len(SP_CompressedModByteHeader))
        
        if buffer == SP_CompressedModByteHeader:
            return (True, SP_CompressedModByteHeader)
        
        with open(modPath, "br") as file:
            buffer = file.read(len(SR_CompressedModByteHeader))
        
        if buffer == SR_CompressedModByteHeader:
            return (True, SR_CompressedModByteHeader)
        
        return (False, None)

    def DecompressMod(modPath):
        CompressedModByteHeader = ModManager.detectCompressedHeader(modPath)[1]
        
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
        if not header.Read(modFilePath): return None

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

        if ModManager.detectCompressedHeader(file)[0]:
            if not ModManager.DecompressMod(file):
                print(f"[ERROR] File {file} is corrupted/not a mod file.")
                return
            # Process decompressed one instead
            file += ".decompressed"

        if not ModManager.LoadAssetBundleFromMod(file, out):
            print(f"[ERROR] Something went wrong while extracting file {file}. Is this really a mod file?")
            return

        if file.endswith(".decompressed"): os.remove(file) # Remove decompressed temp file


if __name__ == "__main__": main()