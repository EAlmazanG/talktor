// Utility helpers for static asset paths. All code and comments in English.

export const ICONS_PATH = "/assets/icons" as const;
export const IMAGES_PATH = "/assets/images" as const;

/** Build a public icon path, e.g. iconPath("info.svg") => "/assets/icons/info.svg" */
export const iconPath = (name: string) => `${ICONS_PATH}/${name}`;

/** Build a public image path, e.g. imagePath("placeholder.svg") => "/assets/images/placeholder.svg" */
export const imagePath = (name: string) => `${IMAGES_PATH}/${name}`;
