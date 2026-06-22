import { useEffect, useRef, type RefObject } from "react";

/**
 * ref-dən kənara klikləyəndə onClose çağırır (mousedown).
 * onClose hər render dəyişsə də listener bir dəfə qurulur (callback ref).
 */
export function useClickOutside<T extends HTMLElement>(
  ref: RefObject<T | null>,
  onClose: () => void,
) {
  const cb = useRef(onClose);
  cb.current = onClose;

  useEffect(() => {
    function onDown(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) cb.current();
    }
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [ref]);
}
