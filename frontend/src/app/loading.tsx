import { RouteSkeleton } from "@/components/layout/RouteSkeleton";

/**
 * Bütün route-lar üçün Suspense fallback-ı. Klik anında dərhal göstərilir,
 * səhifənin JS chunk-ı hazırlanana qədər köhnə səhifə donmur.
 */
export default function Loading() {
  return <RouteSkeleton />;
}
