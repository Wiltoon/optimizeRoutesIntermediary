// Shared TypeScript types matching the backend Pydantic schemas

export interface Point {
  lng: number;
  lat: number;
}

export interface Delivery {
  id: string | number;
  point: Point;
  size: number;
  idu: number;
}

export interface CVRPInstance {
  name: string;
  region: string;
  origin: Point;
  vehicle_capacity: number;
  deliveries: Delivery[];
}

export interface VehicleRoute {
  vehicle_id: number;
  origin: Point;
  deliveries: Delivery[];
}

export interface OptimizeRequest {
  instance: CVRPInstance;
  iterations?: number;
  method?: string;
  city?: string;
}

export interface OptimizeResponse {
  solution_id: string;
  vehicles: VehicleRoute[];
  total_distance_km: number;
  num_vehicles: number;
  time_s: number;
}

export interface VehicleMetrics {
  vehicle_id: number;
  distance_km: number;
  occupation_pct: number;
  num_deliveries: number;
}

export interface MetricsResponse {
  solution_id: string;
  total_distance_km: number;
  num_vehicles: number;
  vehicles: VehicleMetrics[];
  gain_pct: number | null;
}

export interface CompareEntry {
  method: string;
  total_distance_km?: number;
  num_vehicles?: number;
  time_s?: number;
  error?: string;
}

export interface CompareResponse {
  city: string;
  instance_name: string;
  results: CompareEntry[];
}

export interface GeoJSONFeature {
  type: "Feature";
  geometry: {
    type: "LineString" | "Point";
    coordinates: number[][] | number[];
  };
  properties: Record<string, unknown>;
}

export interface GeoJSONResponse {
  type: "FeatureCollection";
  features: GeoJSONFeature[];
}

export interface DynamicBatchEvent {
  batch_index: number;
  vehicles: VehicleRoute[];
  total_distance_km: number;
  num_vehicles: number;
  time_s: number;
  done?: boolean;
}
