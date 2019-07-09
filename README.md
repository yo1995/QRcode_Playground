# QRcode_Playground

📊 A repo with many fascinating project related to QR code

Please refer to https://yo1995.github.io/coding/file-to-GIF/ to learn more about the first two projects.

## SEO

文件转GIF  
文件转动图 分享  
个性化二维码  
彩色二维码  
动图二维码  
动态二维码  
Animated QRcode
File to GIF  
file to qrcode

## QRImage

一个简单的、基于CuteR的多线程彩色动态二维码生成器。

## QRCodec

Convert arbitrary file to an animated GIF and share freely!

Encode a file to a GIF of QR code frames, share with any image hosting service, and decode the GIF back to the original file.

将文件转为二维码动态GIF，上传至图床分享，以打破图床只能分享图片的限制——无拘无束，在任何不压缩GIF的图床分享文件！

### 原理

- 编码

首先将文件转为对应的 base64 字符串表示，然后将字符串按照符合二维码最大利用率的长度分割，并将每个分割后的子串编码为二维码。接着把二维码转为 GIF 的一帧，拼接得到输出 GIF。

- 解码

将 GIF 文件按帧读取，对每一帧进行二维码解码，再将解码后得到的字符串进行拼接，并 base64 解码得到文件的二进制表达，存储到相应路径。
