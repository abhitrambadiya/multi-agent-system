export interface RoomDef {
  id: string;
  name: string;
  x: number;
  y: number;
  w: number;
  h: number;
  floorPattern: string;
  hasGlassWalls: boolean;
}

export interface FurnitureDef {
  id: string;
  type: 'desk' | 'chair' | 'sofa' | 'plant' | 'cabinet' | 'board';
  x: number;
  y: number;
  w?: number;
  h?: number;
  rotation?: number;
  color?: string;
  extra?: Record<string, unknown>;
}

export interface CameraState {
  x: number;
  y: number;
  z: number;
}
