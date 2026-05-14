import type { Place } from '@/types';

declare global {
  interface Window {
    AMap?: any;
    _AMapSecurityConfig?: { securityJsCode: string };
  }
}

let mapInstance: any = null;
let markers: any[] = [];
let loadingPromise: Promise<any> | null = null;

export function hasAmapKey() {
  return Boolean(import.meta.env.VITE_AMAP_KEY);
}

export async function loadAMap() {
  const key = import.meta.env.VITE_AMAP_KEY;
  if (!key) {
    throw new Error('未配置高德地图 Key，使用降级地图视图。');
  }
  if (window.AMap) return window.AMap;
  if (loadingPromise) return loadingPromise;

  const securityCode = import.meta.env.VITE_AMAP_SECURITY_CODE;
  if (securityCode) {
    window._AMapSecurityConfig = { securityJsCode: securityCode };
  }

  loadingPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(key)}`;
    script.async = true;
    script.onload = () => resolve(window.AMap);
    script.onerror = () => reject(new Error('高德地图加载失败，已切换到地点清单。'));
    document.head.appendChild(script);
  });
  return loadingPromise;
}

export async function createMap(containerId: string) {
  const AMap = await loadAMap();
  mapInstance = new AMap.Map(containerId, {
    zoom: 11,
    viewMode: '2D'
  });
  return mapInstance;
}

export function clearMarkers() {
  if (mapInstance && markers.length) {
    mapInstance.remove(markers);
  }
  markers = [];
}

export function addMarkers(places: Place[]) {
  if (!mapInstance || !window.AMap) return;
  clearMarkers();
  const located = places.filter((place) => typeof place.lng === 'number' && typeof place.lat === 'number');
  markers = located.map((place) => {
    const marker = new window.AMap.Marker({
      position: [place.lng, place.lat],
      title: place.name
    });
    const info = new window.AMap.InfoWindow({
      content: `<div class="map-info"><strong>${place.name}</strong><p>${place.type} · ${place.reason}</p></div>`
    });
    marker.on('click', () => info.open(mapInstance, marker.getPosition()));
    return marker;
  });
  if (markers.length) {
    mapInstance.add(markers);
    fitView();
  }
}

export function fitView() {
  if (mapInstance && markers.length) {
    mapInstance.setFitView(markers, false, [40, 40, 40, 40]);
  }
}
