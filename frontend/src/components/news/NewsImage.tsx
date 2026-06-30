"use client";

import { useEffect, useRef, useState } from "react";
import { GeneratedThumb } from "@/components/news/GeneratedThumb";
import type { Category } from "@/types";

/**
 * Xəbər örtüyü — 100% zəmanət: brendli generativ örtük HƏMİŞƏ arxada render olunur,
 * naşirin real og:image-i isə üstündə yüklənəndə fade-in olur. Şəkil yoxdursa,
 * yüklənənə qədər və ya yüklənmə xətasında örtük görünür — heç vaxt boş/qırıq kart olmur.
 */
export function NewsImage({
  src,
  seed,
  category,
  className,
}: {
  src: string | null;
  seed: string;
  category: Category;
  className?: string;
}) {
  const [loaded, setLoaded] = useState(false);
  const [failed, setFailed] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  const showImg = Boolean(src) && !failed;

  // Keşlənmiş şəkildə onLoad handler qoşulmamışdan əvvəl atəşlənə bilər —
  // mount-da `complete` yoxla ki, şəkil opacity-0-da ilişməsin.
  useEffect(() => {
    const el = imgRef.current;
    if (el?.complete && el.naturalWidth > 0) setLoaded(true);
  }, [src]);

  return (
    <div className={`relative ${className ?? ""}`}>
      {/* zəmanətli örtük — həmişə arxada */}
      <div className="absolute inset-0">
        <GeneratedThumb seed={seed} category={category} className="h-full w-full" />
      </div>

      {/* real şəkil — üstdə, hazır olanda fade-in; xətada gizlənir (örtük qalır) */}
      {showImg && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          ref={imgRef}
          src={src as string}
          alt=""
          loading="lazy"
          referrerPolicy="no-referrer"
          onLoad={() => setLoaded(true)}
          onError={() => setFailed(true)}
          className={`absolute inset-0 h-full w-full object-cover transition-opacity duration-500 ${
            loaded ? "opacity-100" : "opacity-0"
          }`}
        />
      )}
    </div>
  );
}
