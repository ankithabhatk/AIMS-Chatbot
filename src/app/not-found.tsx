import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-[100dvh] bg-[#f8f9fa] flex items-center justify-center p-4">
      {/* 
        This recreates the exact specific aesthetics found in the 
        screenshot of the '404 This is not the web page you are looking for'
      */}
      <div className="w-full max-w-4xl flex items-center justify-center relative select-none">
        {/* Background "404" large text */}
        <div 
          className="absolute text-[25vw] md:text-[280px] font-bold text-white selection:bg-transparent"
          style={{
            WebkitTextStroke: '6px #e0e0e0', // Creates the transparent inner text with thick distinct strokes
            opacity: 0.8,
            letterSpacing: '-0.05em',
            zIndex: 0,
            transform: 'translateY(-15%)'
          }}
        >
          404
        </div>

        {/* Foreground message box */}
        <div className="relative z-10 w-full max-w-2xl text-center md:text-left mt-24 md:mt-32">
          <div className="flex bg-white shadow-xl rounded-r-3xl rounded-bl-3xl p-8 md:p-14 border border-gray-50 relative ml-0 md:ml-12 overflow-hidden items-center justify-center">
            
            {/* Subtle background noise texture emulation */}
            <div className="absolute inset-0 opacity-[0.03] z-0 pointer-events-none" style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.65%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E")' }}></div>

            <h1 className="text-[#2b5a7a] font-serif text-4xl md:text-5xl lg:text-[54px] leading-[1.15] font-bold z-10 text-left">
              This is not the<br/>web page you<br/>are looking for.
            </h1>
            
            {/* A subtle arrow accent that is occasionally found in such boxes */}
            <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 w-8 h-8 rotate-45 border-r border-t border-gray-100 bg-white"></div>
          </div>
          
          <div className="mt-8 flex justify-center md:justify-start md:ml-12">
            <Link 
              href="/"
              className="inline-flex items-center text-sm font-medium text-white bg-[#0066cc] hover:bg-[#0052a3] px-6 py-3 rounded-lg shadow-sm transition"
            >
              ← Return Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
