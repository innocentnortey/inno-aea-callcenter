import type { Reaction } from "../scenarios/types";
import { reactions as shared } from "./shared";
import { reactions as scr01core } from "./scr01-core";
import { reactions as scr01cards } from "./scr01-cards";
import { reactions as scr02 } from "./scr02";
import { reactions as scr03 } from "./scr03";
import { reactions as scr04 } from "./scr04";
import { reactions as scr05 } from "./scr05";
import { reactions as scr06 } from "./scr06";
import { reactions as scr07 } from "./scr07";
import { reactions as scr08 } from "./scr08";
import { reactions as scr09 } from "./scr09";
import { reactions as scr10 } from "./scr10";
import { reactions as scr11 } from "./scr11";
import { reactions as scr12 } from "./scr12";

export const reactions: Reaction[] = [
  ...shared, ...scr01core, ...scr01cards, ...scr02, ...scr03, ...scr04, ...scr05, ...scr06, ...scr07, ...scr08, ...scr09, ...scr10, ...scr11, ...scr12,
];
