import AVFoundation
import AppKit
import ScreenSaver

/// Paketin içindeki EyeOfCreation.mp4'ü dikişsiz döngüyle oynatan ekran koruyucu.
@objc(EyeOfCreationView)
final class EyeOfCreationView: ScreenSaverView {
    private var player: AVQueuePlayer?
    private var looper: AVPlayerLooper?
    private var playerLayer: AVPlayerLayer?

    override init?(frame: NSRect, isPreview: Bool) {
        super.init(frame: frame, isPreview: isPreview)
        setup()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        setup()
    }

    private func setup() {
        wantsLayer = true
        layer?.backgroundColor = NSColor.black.cgColor
        animationTimeInterval = 1.0 / 30.0

        let bundle = Bundle(for: EyeOfCreationView.self)
        guard let url = bundle.url(forResource: "EyeOfCreation", withExtension: "mp4") else {
            NSLog("EyeOfCreation: video paketin içinde bulunamadı")
            return
        }

        let queue = AVQueuePlayer()
        queue.isMuted = true
        queue.preventsDisplaySleepDuringVideoPlayback = false
        looper = AVPlayerLooper(player: queue, templateItem: AVPlayerItem(url: url))

        let pl = AVPlayerLayer(player: queue)
        pl.videoGravity = .resizeAspectFill
        pl.frame = bounds
        pl.autoresizingMask = [.layerWidthSizable, .layerHeightSizable]
        layer?.addSublayer(pl)

        player = queue
        playerLayer = pl

        // macOS 14+ ekran koruyucuyu kapatınca süreci açık bırakabiliyor;
        // bu bildirimle oynatmayı durdurup süreci temizliyoruz.
        DistributedNotificationCenter.default().addObserver(
            self,
            selector: #selector(screenSaverWillStop(_:)),
            name: NSNotification.Name("com.apple.screensaver.willstop"),
            object: nil
        )
    }

    override func startAnimation() {
        super.startAnimation()
        player?.play()
    }

    override func stopAnimation() {
        super.stopAnimation()
        player?.pause()
    }

    override func animateOneFrame() {
        // Çizimi AVPlayerLayer yapıyor.
    }

    override func layout() {
        super.layout()
        playerLayer?.frame = bounds
    }

    override var hasConfigureSheet: Bool { false }
    override var configureSheet: NSWindow? { nil }

    @objc private func screenSaverWillStop(_ note: Notification) {
        player?.pause()
        if !isPreview {
            DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) { exit(0) }
        }
    }

    deinit {
        DistributedNotificationCenter.default().removeObserver(self)
    }
}
