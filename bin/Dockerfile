FROM freeslave/vlc-ffmpeg:latest

# install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends binutils python3-pip python3-dev libgtk2.0-dev && \
    apt-get -y clean && \
    rm -rf /var/cache/apt/* /var/lib/apt/lists/*

# install python dependencies
RUN pip3 install --upgrade pip && pip install pyinstaller python-vlc && \
    pip install -f https://extras.wxpython.org/wxPython4/extras/linux/gtk2/debian-8 wxPython

# add build script
CMD pyinstaller --strip --name festengine /src/main.pyw && \
    (cd dist/festengine && \
    rm -f libX*.so* libxcb*.so* \
        libgcc_s.so.1 libstdc++.so.6 \
        libgpg-error.so.0 libexpat.so.1 libz.so.1 libasound.so.2 \
        libICE.so.6 libSM.so.6 \
        libidn.so.11 libuuid.so.1 \
        libglib-2.0.so.0 libgobject-2.0.so.0 libgio-2.0.so.0 \
        libgdk_pixbuf-2.0.so.0 libfontconfig.so.1 libfreetype.so.6 \
        libharfbuzz.so.0 libpangoft2-1.0.so.0 libpangocairo-1.0.so.0 libpango-1.0.so.0 ) && \
    cp /usr/local/lib/libavcodec.so.56.* dist/festengine/libavcodec.so.56 && \
    cp /usr/local/lib/libavformat.so.56.* dist/festengine/libavformat.so.56 && \
    cp /usr/local/lib/libavutil.so.54.* dist/festengine/libavutil.so.54 && \
    cp /usr/local/lib/libswscale.so.3.* dist/festengine/libswscale.so.3 && \
    cp /usr/lib/x86_64-linux-gnu/libx264.so.142 dist/festengine/ && \
    cp /usr/lib/x86_64-linux-gnu/libmatroska.so.6 dist/festengine/ && \
    cp /usr/lib/x86_64-linux-gnu/libebml.so.4 dist/festengine/ && \
    cp /usr/lib/x86_64-linux-gnu/libmpeg2.so.0.* dist/festengine/libmpeg2.so.0 && \
    cp /usr/lib/x86_64-linux-gnu/libmpeg2convert.so.0.* dist/festengine/libmpeg2convert.so.0 && \
    cp /usr/lib/x86_64-linux-gnu/libvorbis.so.0.* dist/festengine/libvorbis.so.0 && \
    cp /usr/lib/x86_64-linux-gnu/libvorbisenc.so.2.* dist/festengine/libvorbisenc.so.2 && \
    cp /usr/lib/x86_64-linux-gnu/libFLAC.so.8.* dist/festengine/libFLAC.so.8 && \
    cp /usr/lib/x86_64-linux-gnu/libva.so.1.* dist/festengine/libva.so.1 && \
    cp -r /usr/local/lib/vlc/ dist/festengine && \
    mv dist/festengine/vlc/libvlc_vdpau.so.0.0.0 dist/festengine/libvlc_vdpau.so.0 && \
    rm dist/festengine/vlc/libvlc_vdpau.* dist/festengine/vlc/vlc-cache-gen dist/festengine/vlc/libcompat.* && \
    cd dist && tar -czf /out/festengine.tar.gz festengine
