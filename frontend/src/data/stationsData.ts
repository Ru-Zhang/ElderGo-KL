import { StationData } from '../app/AppProvider';

export const stationsData: StationData[] = [
  {
    id: '1',
    name: 'KL Sentral',
    wheelchairAccessible: true,
    elevatorAvailable: true,
    ticketCounter: true,
    operatingHours: '6:00 AM - 12:00 AM',
    imageUrl: 'https://images.unsplash.com/photo-1587589185939-ce9ee1f48b0e?w=1200&h=600&fit=crop'
  },
  {
    id: '2',
    name: 'Pasar Seni',
    wheelchairAccessible: true,
    elevatorAvailable: true,
    ticketCounter: true,
    operatingHours: '6:00 AM - 12:00 AM',
    imageUrl: 'https://images.unsplash.com/photo-1587589185939-ce9ee1f48b0e?w=1200&h=600&fit=crop'
  },
  {
    id: '3',
    name: 'Bukit Bintang',
    wheelchairAccessible: true,
    elevatorAvailable: true,
    ticketCounter: true,
    operatingHours: '6:00 AM - 12:00 AM',
    imageUrl: 'https://images.unsplash.com/photo-1587589185939-ce9ee1f48b0e?w=1200&h=600&fit=crop'
  },
  {
    id: '4',
    name: 'SunU-Monash',
    wheelchairAccessible: true,
    elevatorAvailable: true,
    ticketCounter: false,
    operatingHours: '6:00 AM - 11:00 PM',
    imageUrl: 'https://images.unsplash.com/photo-1587589185939-ce9ee1f48b0e?w=1200&h=600&fit=crop'
  },
  {
    id: '5',
    name: 'KLCC',
    wheelchairAccessible: true,
    elevatorAvailable: true,
    ticketCounter: true,
    operatingHours: '6:00 AM - 12:00 AM',
    imageUrl: 'https://images.unsplash.com/photo-1587589185939-ce9ee1f48b0e?w=1200&h=600&fit=crop'
  },
  {
    id: '6',
    name: 'Mid Valley',
    wheelchairAccessible: false,
    elevatorAvailable: false,
    ticketCounter: true,
    operatingHours: '6:00 AM - 11:30 PM',
    imageUrl: 'https://images.unsplash.com/photo-1587589185939-ce9ee1f48b0e?w=1200&h=600&fit=crop'
  },
  {
    id: '7',
    name: 'Bandaraya',
    wheelchairAccessible: true,
    elevatorAvailable: true,
    ticketCounter: false,
    operatingHours: '6:00 AM - 12:00 AM',
    imageUrl: 'https://images.unsplash.com/photo-1587589185939-ce9ee1f48b0e?w=1200&h=600&fit=crop'
  },
  {
    id: '8',
    name: 'Dang Wangi',
    wheelchairAccessible: true,
    elevatorAvailable: true,
    ticketCounter: true,
    operatingHours: '6:00 AM - 12:00 AM',
    imageUrl: 'https://images.unsplash.com/photo-1587589185939-ce9ee1f48b0e?w=1200&h=600&fit=crop'
  }
];

export const getPopularStations = (): StationData[] => {
  return stationsData.slice(0, 4);
};

export const searchStations = (query: string): StationData[] => {
  if (!query.trim()) {
    return [];
  }

  return stationsData.filter(station =>
    station.name.toLowerCase().includes(query.toLowerCase())
  );
};

export const getStationById = (id: string): StationData | null => {
  return stationsData.find(station => station.id === id) || null;
};
