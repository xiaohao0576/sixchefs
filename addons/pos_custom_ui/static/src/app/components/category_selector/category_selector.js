import { patch } from "@web/core/utils/patch";
import { CategorySelector } from "@point_of_sale/app/components/category_selector/category_selector";

const sortCategories = (categories) =>
    [...categories].sort((a, b) => a.sequence - b.sequence || a.name.localeCompare(b.name));

patch(CategorySelector.prototype, {
    // Only 2 levels of categories are supported (root + direct children).
    // - No selection: show root categories only.
    // - A root or child category selected: show only that root category and its children.
    getCategoriesAndSub() {
        const selectedCategory = this.pos.selectedCategory;
        if (!selectedCategory) {
            return sortCategories(this.pos.rootCategories)
                .filter((c) => c.hasProductsToShow)
                .map(this.getChildCategoriesInfo, this);
        }
        const rootCategory = selectedCategory.parent_id || selectedCategory;
        const categories = [rootCategory, ...sortCategories(rootCategory.child_ids || [])];
        return categories.filter((c) => c.hasProductsToShow).map(this.getChildCategoriesInfo, this);
    },
});
