param([string]$AssetDirectory = "$PSScriptRoot/assets/habitats")

# Deterministic matte extraction. Original PNGs remain untouched.
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

public static class HabitatMatte {
  static bool White(byte[] pixels, int p) {
    int i = p * 4;
    int lo = Math.Min(pixels[i], Math.Min(pixels[i+1], pixels[i+2]));
    int hi = Math.Max(pixels[i], Math.Max(pixels[i+1], pixels[i+2]));
    return lo >= 248 && hi - lo <= 4;
  }

  public static string Extract(string source, string destination, string preview) {
    using (var original = new Bitmap(source))
    using (var image = new Bitmap(original.Width, original.Height, PixelFormat.Format32bppArgb)) {
      using (var graphics = Graphics.FromImage(image)) graphics.DrawImageUnscaled(original, 0, 0);
      int w = image.Width, h = image.Height, count = w * h;
      var pixels = new byte[count * 4];
      var locked = image.LockBits(new Rectangle(0,0,w,h), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
      for (int y = 0; y < h; y++) Marshal.Copy(IntPtr.Add(locked.Scan0,y * locked.Stride), pixels, y * w * 4, w * 4);
      image.UnlockBits(locked);
      var mask = new byte[count]; var queue = new int[count]; int tail = 0;
      Action<int> add = p => { if (mask[p] == 0 && White(pixels,p)) { mask[p] = 1; queue[tail++] = p; } };
      for (int x = 0; x < w; x++) { add(x); add((h-1)*w+x); }
      for (int y = 0; y < h; y++) { add(y*w); add(y*w+w-1); }
      for (int head = 0; head < tail; head++) {
        int p = queue[head], x = p % w, y = p / w;
        for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) {
          int nx=x+dx, ny=y+dy;
          if (nx>=0 && nx<w && ny>=0 && ny<h) add(ny*w+nx);
        }
      }
      var result = (byte[])pixels.Clone();
      int minX=w, minY=h, maxX=0, maxY=0, soft=0;
      for (int y=0; y<h; y++) for (int x=0; x<w; x++) {
        int p=y*w+x, i=p*4;
        if(mask[p]!=0) { result[i+3]=0; continue; }
        minX=Math.Min(minX,x); minY=Math.Min(minY,y); maxX=Math.Max(maxX,x); maxY=Math.Max(maxY,y);
        bool edge=false;
        for(int dy=-1; dy<=1 && !edge; dy++) for(int dx=-1; dx<=1; dx++) {
          int nx=x+dx, ny=y+dy;
          if(nx>=0 && nx<w && ny>=0 && ny<h && mask[ny*w+nx]!=0) { edge=true; break; }
        }
        // Decontaminate only the near-white antialiased boundary, not white hull interiors.
        if(!edge || Math.Min(pixels[i],Math.Min(pixels[i+1],pixels[i+2]))<225) continue;
        int best=p, luminance=pixels[i]+pixels[i+1]+pixels[i+2];
        for(int dy=-2;dy<=2;dy++) for(int dx=-2;dx<=2;dx++) {
          int nx=x+dx,ny=y+dy;
          if(nx<0||nx>=w||ny<0||ny>=h)continue;
          int n=ny*w+nx,j=n*4,sum=pixels[j]+pixels[j+1]+pixels[j+2];
          if(mask[n]==0 && sum<luminance) { best=n; luminance=sum; }
        }
        double alpha=0;
        for(int channel=0;channel<3;channel++) {
          double denominator=255-pixels[best*4+channel];
          if(denominator>0)alpha=Math.Max(alpha,(255-pixels[i+channel])/denominator);
        }
        if(alpha<=0 || alpha>=.98)continue;
        alpha=Math.Max(.05,alpha); result[i+3]=(byte)Math.Round(alpha*255); soft++;
        for(int channel=0;channel<3;channel++) result[i+channel]=(byte)Math.Max(0,Math.Min(255,Math.Round((pixels[i+channel]-255*(1-alpha))/alpha)));
      }
      if(minX>maxX || minY>maxY)throw new InvalidOperationException("No foreground found");
      int left=Math.Max(0,minX-12),top=Math.Max(0,minY-12),right=Math.Min(w-1,maxX+12),bottom=Math.Min(h-1,maxY+12);
      int outW=right-left+1,outH=bottom-top+1;
      using(var output=new Bitmap(outW,outH,PixelFormat.Format32bppArgb)) {
        var data=output.LockBits(new Rectangle(0,0,outW,outH),ImageLockMode.WriteOnly,PixelFormat.Format32bppArgb);
        for(int y=0;y<outH;y++)Marshal.Copy(result,((y+top)*w+left)*4,IntPtr.Add(data.Scan0,y*data.Stride),outW*4);
        output.UnlockBits(data);output.Save(destination,ImageFormat.Png);
        int pw=Math.Min(1000,outW),ph=(int)Math.Round(outH*(double)pw/outW);
        using(var check=new Bitmap(pw,ph))using(var g=Graphics.FromImage(check)) {
          g.Clear(Color.FromArgb(5,8,17));g.InterpolationMode=System.Drawing.Drawing2D.InterpolationMode.HighQualityBicubic;
          g.DrawImage(output,new Rectangle(0,0,pw,ph));check.Save(preview,ImageFormat.Png);
        }
      }
      return String.Format("{0}x{1}; background={2}; softEdges={3}",outW,outH,tail,soft);
    }
  }
}
'@

$reportDirectory = Join-Path $PSScriptRoot '../build/reports/habitat-transparent'
New-Item -ItemType Directory -Force -Path $reportDirectory | Out-Null
foreach ($habitatName in @('orion', 'mars-base', 'iss')) {
  $originalPath = Join-Path $AssetDirectory "$habitatName.png"
  $cutoutPath = Join-Path $AssetDirectory "$habitatName-transparent.png"
  $previewPath = Join-Path $reportDirectory "$habitatName-preview.png"
  $result = [HabitatMatte]::Extract($originalPath, $cutoutPath, $previewPath)
  Write-Output "$habitatName : $result"
}
