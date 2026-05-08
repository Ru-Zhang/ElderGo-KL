import type { LucideIcon } from 'lucide-react';
import {
  Accessibility,
  Bus,
  CircleDot,
  Coffee,
  CreditCard,
  Droplets,
  Building2,
  ParkingCircle,
  ShoppingBag,
  Ticket,
  TrainFront,
} from 'lucide-react';

/**
 * Map scraped facility labels (English, from mrt.com.my) to icons for chip UI.
 */
export function pickFacilityIcon(label: string): LucideIcon {
  const l = label.toLowerCase();
  if (l.includes('lift') || l.includes('escalator')) return Accessibility;
  if (l.includes('toilet')) return Droplets;
  if (l.includes('ticket') || l.includes('vending')) return Ticket;
  if (l.includes('shop') || l.includes('mall')) return ShoppingBag;
  if (l.includes('bus') || l.includes('hub')) return Bus;
  if (l.includes('rail') || l.includes('platform') || l.includes('interchange') || l.includes('ktm'))
    return TrainFront;
  if (l.includes('customer') || l.includes('office')) return Building2;
  if (l.includes('park') && l.includes('car')) return ParkingCircle;
  if (l.includes('atm') || l.includes('tng') || l.includes('reload')) return CreditCard;
  if (l.includes('drink')) return Coffee;
  return CircleDot;
}
