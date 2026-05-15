import { cleanStationQuery } from './stationName';

import type { RouteStationImage } from '../services/routeStationImages';



export function normalizeRouteKeyPart(value: string): string {

  return value.trim().toLowerCase().replace(/\s+/g, ' ');

}



export function buildRouteKey(origin: string, destination: string): string {

  return `${normalizeRouteKeyPart(origin)}|${normalizeRouteKeyPart(destination)}`;

}



export function normalizeStationLookupKey(station: string): string {

  return normalizeRouteKeyPart(station);

}



export function hasStepBasedRouteImages(imageMap: Record<string, RouteStationImage[]>): boolean {

  return Object.keys(imageMap).some((key) => /^step:\d+$/.test(key));

}



export function getCustomRouteStepImages(

  imageMap: Record<string, RouteStationImage[]>,

  stepIndex: number,

): RouteStationImage[] {

  if (!hasStepBasedRouteImages(imageMap) || stepIndex < 0) return [];

  return imageMap[`step:${stepIndex + 1}`] ?? [];

}



export function getCustomStationImages(

  imageMap: Record<string, RouteStationImage[]>,

  stationRaw: string | null | undefined,

): RouteStationImage[] {

  if (!stationRaw) return [];

  const cleaned = cleanStationQuery(stationRaw) || stationRaw;

  const normalized = normalizeStationLookupKey(cleaned);

  const compact = normalized.replace(/\s+/g, '');

  return imageMap[normalized] ?? imageMap[compact] ?? [];

}



export function toPathOnlyImages(images: RouteStationImage[]): string[] {

  return images.map((image) => image.path);

}



/** Turn API/static paths into absolute URLs for canvas export. */

export function resolveRouteImageUrl(path: string): string {

  if (!path) return path;

  if (path.startsWith('http://') || path.startsWith('https://')) return path;

  if (path.startsWith('/')) {

    return `${window.location.origin}${path}`;

  }

  return path;

}


